import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import Base, engine
from app.main import app
from app.services import schema_introspection


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Same cross-loop asyncpg/psycopg pitfall as the other two projects in this session:
    # pytest-asyncio gives each test function its own event loop by default, but this
    # module-level engine's connection pool is bound to whichever loop first used it.
    await engine.dispose()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    res = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def analytics_sample_data():
    """A throwaway `analytics.test_customers` table for schema-introspection and
    read-only-role tests. Deliberately named to never collide with (or destructively
    touch) whatever the real seed script has populated in `analytics.customers`."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        await conn.execute(text("DROP TABLE IF EXISTS analytics.test_customers CASCADE"))
        await conn.execute(
            text(
                "CREATE TABLE analytics.test_customers ("
                "id SERIAL PRIMARY KEY, name TEXT, email TEXT, segment TEXT, "
                "country TEXT, signup_date DATE)"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO analytics.test_customers (name, email, segment, country, signup_date) VALUES "
                "('Alice', 'alice@test.com', 'SMB', 'US', '2024-01-01'), "
                "('Bob', 'bob@test.com', 'Enterprise', 'UK', '2024-02-01')"
            )
        )

    schema_introspection._schema_cache = None
    await schema_introspection.get_analytics_schema(force_refresh=True)

    yield

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS analytics.test_customers CASCADE"))
    schema_introspection._schema_cache = None
