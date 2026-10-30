import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SqlGeneration(BaseModel):
    """Structured output the LLM must produce when generating SQL from a question."""

    sql: str = Field(description="A single read-only PostgreSQL SELECT statement that answers the question.")
    explanation: str = Field(description="One or two plain-English sentences explaining what the query does.")


class ChartSpec(BaseModel):
    """Structured output the LLM must produce when choosing how to visualize a result set."""

    chart_type: Literal["bar", "line", "pie", "area", "table"] = Field(
        description="table if the result isn't naturally chartable (too many columns, no clear metric)."
    )
    title: str
    x_key: str | None = Field(default=None, description="Column name for the X axis / category / pie label.")
    y_keys: list[str] = Field(default_factory=list, description="Column name(s) for the Y axis / metric(s).")
    insight: str = Field(default="", description="One-sentence takeaway from the data, in plain English.")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    sql: str
    explanation: str | None
    columns: list[str] = []
    rows: list[dict] = []
    row_count: int
    chart_spec: ChartSpec | None
    status: str
    error_message: str | None
    created_at: datetime


class SavedQuerySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    sql: str
    status: str
    row_count: int
    created_at: datetime


class TableSchema(BaseModel):
    table: str
    columns: list[dict]
