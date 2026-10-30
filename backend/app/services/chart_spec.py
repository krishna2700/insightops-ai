from langchain_core.prompts import ChatPromptTemplate

from app.schemas.query import ChartSpec
from app.services.llm import get_llm

CHART_SYSTEM_PROMPT = """You choose how to visualize a SQL query result for a business dashboard.

Given the user's question, the SQL that produced it, the result columns, and a small sample of
rows, pick the best chart type and axis mapping. Use "table" if the result has more than two
meaningful dimensions, is a single row/value, or has no obvious metric to plot. x_key and every
entry in y_keys must be exact column names from the result -- never invent a column name.
"""


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _fallback_chart_spec(columns: list[str], rows: list[dict]) -> ChartSpec:
    """Used when the LLM is unavailable or returns something unusable -- a simple,
    deterministic heuristic so the feature degrades gracefully instead of failing."""
    if len(columns) == 2 and rows and _is_numeric(rows[0].get(columns[1])):
        return ChartSpec(chart_type="bar", title="Result", x_key=columns[0], y_keys=[columns[1]])
    return ChartSpec(chart_type="table", title="Result", x_key=None, y_keys=[])


async def generate_chart_spec(
    question: str, sql: str, columns: list[str], sample_rows: list[dict]
) -> ChartSpec:
    llm = get_llm()
    if llm is None or not columns:
        return _fallback_chart_spec(columns, sample_rows)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHART_SYSTEM_PROMPT),
        ("human", "Question: {question}\n\nSQL: {sql}\n\nColumns: {columns}\n\nSample rows: {sample}"),
    ])
    structured_llm = llm.with_structured_output(ChartSpec)
    chain = prompt | structured_llm

    try:
        spec = await chain.ainvoke(
            {"question": question, "sql": sql, "columns": columns, "sample": sample_rows[:5]}
        )
    except Exception:  # noqa: BLE001 - never fail the whole request over chart selection
        return _fallback_chart_spec(columns, sample_rows)

    valid_columns = set(columns)
    if spec.x_key and spec.x_key not in valid_columns:
        spec.x_key = None
    spec.y_keys = [k for k in spec.y_keys if k in valid_columns]
    if spec.chart_type != "table" and (not spec.y_keys or (spec.chart_type != "pie" and not spec.x_key)):
        return _fallback_chart_spec(columns, sample_rows)

    return spec
