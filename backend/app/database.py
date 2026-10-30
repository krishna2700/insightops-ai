from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Full-access engine: owns the `app` schema (users, saved_queries, dashboards, widgets).
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Read-only engine: connects as `analytics_readonly`, which Postgres itself restricts to
# SELECT on the `analytics` schema (see backend/db-init/01-init.sql). This is the only
# engine the NL->SQL query executor and schema introspector ever touch.
analytics_engine = create_async_engine(settings.analytics_database_url, pool_pre_ping=True)


class Base(DeclarativeBase):
    metadata = MetaData(schema="app")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
