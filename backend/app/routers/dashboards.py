import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.dashboard import Dashboard, DashboardWidget
from app.models.saved_query import SavedQuery
from app.models.user import User
from app.schemas.dashboard import DashboardCreate, DashboardDetail, DashboardSummary, WidgetCreate, WidgetResult
from app.services.nl_to_sql import execute_sql
from app.services.response_builders import build_query_response

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])


@router.get("", response_model=list[DashboardSummary])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Dashboard]:
    stmt = select(Dashboard).where(Dashboard.user_id == current_user.id).order_by(Dashboard.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


@router.post("", response_model=DashboardSummary, status_code=201)
async def create_dashboard(
    payload: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dashboard:
    dashboard = Dashboard(user_id=current_user.id, name=payload.name)
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    return dashboard


async def _get_owned_dashboard(dashboard_id: uuid.UUID, current_user: User, db: AsyncSession) -> Dashboard:
    stmt = (
        select(Dashboard)
        .options(selectinload(Dashboard.widgets).selectinload(DashboardWidget.dashboard))
        .where(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id)
    )
    dashboard = (await db.execute(stmt)).scalars().first()
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardDetail)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardDetail:
    dashboard = await _get_owned_dashboard(dashboard_id, current_user, db)

    saved_query_ids = [w.saved_query_id for w in dashboard.widgets]
    saved_queries: dict[uuid.UUID, SavedQuery] = {}
    if saved_query_ids:
        rows = (
            await db.execute(select(SavedQuery).where(SavedQuery.id.in_(saved_query_ids)))
        ).scalars().all()
        saved_queries = {sq.id: sq for sq in rows}

    async def _build_widget(widget: DashboardWidget) -> WidgetResult | None:
        saved = saved_queries.get(widget.saved_query_id)
        if saved is None:
            return None

        rows: list[dict] = []
        if saved.status == "success":
            try:
                _, rows = await execute_sql(saved.sql)
            except Exception:  # noqa: BLE001 - a stale/broken widget shouldn't 500 the whole dashboard
                rows = []
        return WidgetResult(
            id=widget.id, position=widget.position, query=build_query_response(saved, rows=rows)
        )

    results = await asyncio.gather(*[_build_widget(w) for w in dashboard.widgets])
    widgets = [w for w in results if w is not None]

    return DashboardDetail(
        id=dashboard.id, name=dashboard.name, created_at=dashboard.created_at, widgets=widgets
    )


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    dashboard = await _get_owned_dashboard(dashboard_id, current_user, db)
    await db.delete(dashboard)
    await db.commit()


@router.post("/{dashboard_id}/widgets", status_code=201)
async def add_widget(
    dashboard_id: uuid.UUID,
    payload: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    dashboard = await _get_owned_dashboard(dashboard_id, current_user, db)

    saved = (
        await db.execute(
            select(SavedQuery).where(
                SavedQuery.id == payload.saved_query_id, SavedQuery.user_id == current_user.id
            )
        )
    ).scalars().first()
    if saved is None:
        raise HTTPException(status_code=404, detail="Saved query not found")

    next_position = (
        await db.execute(select(func.coalesce(func.max(DashboardWidget.position), -1) + 1).where(
            DashboardWidget.dashboard_id == dashboard.id
        ))
    ).scalar_one()

    widget = DashboardWidget(dashboard_id=dashboard.id, saved_query_id=saved.id, position=next_position)
    db.add(widget)
    await db.commit()
    return {"id": widget.id, "position": widget.position}


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def remove_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_owned_dashboard(dashboard_id, current_user, db)
    widget = (
        await db.execute(
            select(DashboardWidget).where(
                DashboardWidget.id == widget_id, DashboardWidget.dashboard_id == dashboard_id
            )
        )
    ).scalars().first()
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    await db.delete(widget)
    await db.commit()
