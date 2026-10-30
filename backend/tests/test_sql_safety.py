import pytest

from app.services.sql_safety import SqlSafetyError, validate_and_limit


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM analytics.customers",
        "SELECT name FROM analytics.customers LIMIT 10",
        "SELECT c.name, COUNT(*) FROM analytics.customers c "
        "JOIN analytics.orders o ON o.customer_id = c.id GROUP BY c.name",
        "WITH recent AS (SELECT * FROM analytics.orders) SELECT * FROM recent",
    ],
)
def test_allows_legitimate_select_queries(sql):
    result = validate_and_limit(sql, max_rows=500)
    assert result.strip().upper().startswith(("SELECT", "WITH"))


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM analytics.customers",
        "DROP TABLE analytics.customers",
        "UPDATE analytics.customers SET name = 'x'",
        "TRUNCATE analytics.customers",
        "CREATE TABLE evil (id int)",
        "GRANT ALL ON analytics.customers TO public",
    ],
)
def test_rejects_non_select_statements(sql):
    with pytest.raises(SqlSafetyError):
        validate_and_limit(sql, max_rows=500)


def test_rejects_statement_stacking():
    with pytest.raises(SqlSafetyError, match="single SQL statement"):
        validate_and_limit("SELECT 1; DROP TABLE analytics.customers;", max_rows=500)


def test_rejects_data_modifying_cte():
    """Postgres allows `WITH x AS (DELETE ... RETURNING *) SELECT * FROM x` -- a single
    statement whose outer shape is SELECT but which deletes data. The validator must walk
    the whole parse tree, not just check the top-level node type."""
    sql = "WITH deleted AS (DELETE FROM analytics.customers RETURNING *) SELECT * FROM deleted"
    with pytest.raises(SqlSafetyError, match="disallowed operation"):
        validate_and_limit(sql, max_rows=500)


def test_rejects_dangerous_functions():
    with pytest.raises(SqlSafetyError, match="disallowed function"):
        validate_and_limit("SELECT pg_sleep(10)", max_rows=500)


def test_rejects_cross_schema_access():
    with pytest.raises(SqlSafetyError, match="only 'analytics' is queryable"):
        validate_and_limit("SELECT * FROM app.users", max_rows=500)


def test_injects_limit_when_missing():
    result = validate_and_limit("SELECT * FROM analytics.customers", max_rows=50)
    assert "LIMIT 50" in result


def test_clamps_limit_above_max():
    result = validate_and_limit("SELECT * FROM analytics.customers LIMIT 999999", max_rows=50)
    assert "LIMIT 50" in result
    assert "999999" not in result


def test_preserves_limit_below_max():
    result = validate_and_limit("SELECT * FROM analytics.customers LIMIT 5", max_rows=500)
    assert "LIMIT 5" in result


def test_rejects_unparseable_sql():
    with pytest.raises(SqlSafetyError):
        validate_and_limit("THIS IS NOT valid !!! SQL ???", max_rows=500)
