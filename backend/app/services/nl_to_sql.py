from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text

from app.config import get_settings
from app.database import analytics_engine
from app.schemas.query import SqlGeneration
from app.services.llm import get_llm
from app.services.schema_introspection import format_schema_for_prompt, get_analytics_schema
from app.services.sql_safety import SqlSafetyError, validate_and_limit

SQL_SYSTEM_PROMPT = """You are a senior data analyst generating PostgreSQL queries for a business \
analytics dashboard.

Rules:
- Output exactly one read-only SELECT statement against the `analytics` schema described below.
- Never write to the database: no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, or \
data-modifying CTEs.
- Only reference tables and columns that actually appear in the schema below. Never invent a column.
- Prefer explicit column lists over SELECT *.
- Use clear table aliases in joins.
- If the question is ambiguous, make a reasonable assumption and say so in the explanation.

Schema:
{schema}
"""


class NlToSqlError(Exception):
    def __init__(self, message: str, sql: str | None = None):
        super().__init__(message)
        self.sql = sql


async def _generate(question: str, retry_context: str | None = None) -> SqlGeneration:
    llm = get_llm()
    if llm is None:
        raise NlToSqlError("The query engine isn't configured yet -- add OPENAI_API_KEY to enable it.")

    tables = await get_analytics_schema()
    schema_text = format_schema_for_prompt(tables)

    human_message = "{question}" if not retry_context else "{question}\n\n{retry_context}"
    prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("human", human_message),
    ])
    structured_llm = llm.with_structured_output(SqlGeneration)
    chain = prompt | structured_llm

    params = {"schema": schema_text, "question": question}
    if retry_context:
        params["retry_context"] = retry_context

    return await chain.ainvoke(params)


async def execute_sql(sql: str) -> tuple[list[str], list[dict]]:
    settings = get_settings()
    timeout_ms = settings.query_timeout_seconds * 1000

    async with analytics_engine.connect() as conn:
        async with conn.begin():
            # SET LOCAL is transaction-scoped: it cannot leak into the next query that
            # reuses this pooled connection, unlike a plain session-level SET.
            await conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
            result = await conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

    return columns, rows


async def run_nl_query(question: str) -> dict:
    """Generates SQL for `question`, validates it, and executes it. If execution fails
    (e.g. a subtly wrong column name the validator can't catch), makes exactly one
    self-correction attempt with the database's own error fed back to the model."""
    settings = get_settings()
    generation = await _generate(question)

    try:
        safe_sql = validate_and_limit(generation.sql, settings.max_result_rows)
    except SqlSafetyError as exc:
        raise NlToSqlError(f"Generated SQL failed safety validation: {exc}", sql=generation.sql) from exc

    try:
        columns, rows = await execute_sql(safe_sql)
    except NlToSqlError:
        raise
    except Exception as exc:  # noqa: BLE001 - any DB execution failure triggers one retry
        retry_context = f"Your previous SQL failed:\n{generation.sql}\n\nDatabase error:\n{exc}\n\nFix it."
        generation = await _generate(question, retry_context=retry_context)
        try:
            safe_sql = validate_and_limit(generation.sql, settings.max_result_rows)
        except SqlSafetyError as safety_exc:
            raise NlToSqlError(
                f"Generated SQL failed safety validation: {safety_exc}", sql=generation.sql
            ) from safety_exc
        columns, rows = await execute_sql(safe_sql)

    return {
        "sql": safe_sql,
        "explanation": generation.explanation,
        "columns": columns,
        "rows": rows,
    }
