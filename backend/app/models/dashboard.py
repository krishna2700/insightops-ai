from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Dashboard(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboards"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app.users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    widgets: Mapped[list["DashboardWidget"]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan", order_by="DashboardWidget.position"
    )


class DashboardWidget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app.dashboards.id"), nullable=False
    )
    saved_query_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app.saved_queries.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    dashboard: Mapped["Dashboard"] = relationship(back_populates="widgets")
