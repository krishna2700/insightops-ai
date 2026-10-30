import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.query import QueryResponse


class DashboardCreate(BaseModel):
    name: str


class DashboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class WidgetCreate(BaseModel):
    saved_query_id: uuid.UUID


class WidgetResult(BaseModel):
    id: uuid.UUID
    position: int
    query: QueryResponse


class DashboardDetail(DashboardSummary):
    widgets: list[WidgetResult] = []
