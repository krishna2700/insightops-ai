"""Validates LLM-generated SQL before it ever reaches the database.

This is defense in depth, not the only layer: the query also runs through the
`analytics_readonly` Postgres role, which is physically incapable of writing data
(see backend/db-init/01-init.sql). Even so, this module exists because:

  1. A write-capable role would still be dangerous without it (belt + suspenders).
  2. Postgres allows *data-modifying CTEs* -- `WITH x AS (DELETE FROM t RETURNING *)
     SELECT * FROM x` is a syntactically valid single statement whose top-level shape
     is a SELECT. Checking only the outermost node type is not sufficient; every node
     in the parsed tree is inspected.
  3. It gives callers a fast, specific error instead of an opaque permission-denied
     exception from Postgres.
"""

import sqlglot
from sqlglot import exp

ANALYTICS_SCHEMA = "analytics"

_FORBIDDEN_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Grant,
    exp.Command,  # catch-all sqlglot uses for statements it can't otherwise classify
    exp.Into,  # SELECT ... INTO creates a table
)

# Functions with no legitimate place in a read-only analytics query.
_FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "dblink",
    "dblink_exec",
    "lo_import",
    "lo_export",
    "copy",
    "pg_reload_conf",
}


class SqlSafetyError(ValueError):
    pass


def validate_and_limit(sql: str, max_rows: int) -> str:
    """Raises SqlSafetyError if `sql` is anything other than a single, read-only SELECT
    scoped to the `analytics` schema. Otherwise returns the SQL with a LIMIT clause
    added or clamped down to `max_rows`."""
    sql = sql.strip().rstrip(";")

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as exc:  # noqa: BLE001 - surface the parser's own message
        raise SqlSafetyError(f"Could not parse the generated SQL: {exc}") from exc

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise SqlSafetyError("Only a single SQL statement is allowed (no statement stacking).")

    root = statements[0]
    if not isinstance(root, exp.Select):
        raise SqlSafetyError("Only SELECT statements are allowed.")

    for node in root.walk():
        if isinstance(node, _FORBIDDEN_NODE_TYPES):
            raise SqlSafetyError(f"Query contains a disallowed operation: {type(node).__name__}.")

        if isinstance(node, (exp.Func, exp.Anonymous)):
            func_name = (node.name or "").lower()
            if func_name in _FORBIDDEN_FUNCTIONS:
                raise SqlSafetyError(f"Query calls a disallowed function: {func_name}().")

        if isinstance(node, exp.Table) and node.db and node.db.lower() not in ("", ANALYTICS_SCHEMA):
            raise SqlSafetyError(
                f"Query references schema '{node.db}' -- only '{ANALYTICS_SCHEMA}' is queryable."
            )

    existing_limit = root.args.get("limit")
    if existing_limit is not None:
        try:
            requested = int(existing_limit.expression.this)
            if requested > max_rows:
                root.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
        except (TypeError, ValueError, AttributeError):
            root.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
    else:
        root = root.limit(max_rows)

    return root.sql(dialect="postgres")
