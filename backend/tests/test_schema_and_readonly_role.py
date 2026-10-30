import pytest
from httpx import AsyncClient

from app.services.nl_to_sql import execute_sql


async def test_schema_endpoint_reflects_analytics_tables(
    client: AsyncClient, auth_headers: dict[str, str], analytics_sample_data
):
    res = await client.get("/api/schema", headers=auth_headers)
    assert res.status_code == 200

    tables = {t["table"]: t for t in res.json()}
    assert "test_customers" in tables
    column_names = {c["name"] for c in tables["test_customers"]["columns"]}
    assert {"id", "name", "email", "segment", "country", "signup_date"} <= column_names


async def test_readonly_role_can_select(analytics_sample_data):
    columns, rows = await execute_sql("SELECT name FROM analytics.test_customers ORDER BY name")
    assert columns == ["name"]
    assert [r["name"] for r in rows] == ["Alice", "Bob"]


async def test_readonly_role_cannot_write(analytics_sample_data):
    """Enforced by Postgres itself (see backend/db-init/01-init.sql), independent of the
    sql_safety validator -- this is the belt-and-suspenders layer, tested directly."""
    with pytest.raises(Exception, match="permission denied"):
        await execute_sql(
            "INSERT INTO analytics.test_customers (name, email, segment, country, signup_date) "
            "VALUES ('Evil', 'evil@test.com', 'SMB', 'US', '2024-01-01')"
        )


async def test_query_endpoint_fails_clearly_without_openai_key(
    client: AsyncClient, auth_headers: dict[str, str], analytics_sample_data
):
    """With OPENAI_API_KEY unset (the default in CI), the endpoint must return a clear,
    actionable error rather than a generic 500."""
    res = await client.post("/api/query", headers=auth_headers, json={"question": "How many customers?"})
    assert res.status_code == 422
    assert "OPENAI_API_KEY" in res.json()["detail"]
