from sqlalchemy import inspect

from app.database import analytics_engine

ANALYTICS_SCHEMA = "analytics"

_schema_cache: list[dict] | None = None


async def get_analytics_schema(force_refresh: bool = False) -> list[dict]:
    """Introspects the `analytics` schema's tables/columns via the read-only connection.
    Cached in-process since the sample dataset's shape doesn't change at runtime; pass
    force_refresh=True after a schema migration."""
    global _schema_cache
    if _schema_cache is not None and not force_refresh:
        return _schema_cache

    def _introspect(sync_conn) -> list[dict]:
        inspector = inspect(sync_conn)
        tables = []
        for table_name in inspector.get_table_names(schema=ANALYTICS_SCHEMA):
            columns = [
                {"name": col["name"], "type": str(col["type"]), "nullable": col["nullable"]}
                for col in inspector.get_columns(table_name, schema=ANALYTICS_SCHEMA)
            ]
            fks = [
                {
                    "columns": fk["constrained_columns"],
                    "references_table": fk["referred_table"],
                    "references_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table_name, schema=ANALYTICS_SCHEMA)
            ]
            tables.append({"table": table_name, "columns": columns, "foreign_keys": fks})
        return tables

    async with analytics_engine.connect() as conn:
        tables = await conn.run_sync(_introspect)

    _schema_cache = tables
    return tables


def format_schema_for_prompt(tables: list[dict]) -> str:
    """Renders the introspected schema as compact DDL-like text for the LLM prompt."""
    lines = []
    for table in tables:
        cols = ", ".join(f"{c['name']} {c['type']}" for c in table["columns"])
        lines.append(f"TABLE analytics.{table['table']} ({cols})")
        for fk in table["foreign_keys"]:
            lines.append(
                f"  FK: {table['table']}.{','.join(fk['columns'])} -> "
                f"{fk['references_table']}.{','.join(fk['references_columns'])}"
            )
    return "\n".join(lines)
