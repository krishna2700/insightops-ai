from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SavedQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One natural-language query turn: the question, the SQL the model generated for it,
    and the chart it picked. Result *rows* are intentionally not persisted here -- widgets
    re-run the stored SQL on load so dashboards always show live data, not a stale snapshot.
    """

    __tablename__ = "saved_queries"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    sql: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    chart_spec: Mapped[dict] = mapped_column(JSON, nullable=True)
    columns: Mapped[list] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success | error
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
