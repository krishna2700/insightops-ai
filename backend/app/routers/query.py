import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.dashboard import DashboardWidget
from app.models.saved_query import SavedQuery
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse, SavedQuerySummary, TableSchema
from app.services.chart_spec import generate_chart_spec
from app.services.nl_to_sql import NlToSqlError, execute_sql, run_nl_query
from app.services.response_builders import build_query_response
from app.services.schema_introspection import get_analytics_schema

router = APIRouter(prefix="/api", tags=["query"])


@router.get("/schema", response_model=list[TableSchema])
async def get_schema(_: User = Depends(get_current_user)) -> list[dict]:
    return await get_analytics_schema()


@router.post("/query", response_model=QueryResponse)
async def run_query(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedQuery:
    try:
        result = await run_nl_query(payload.question)
    except NlToSqlError as exc:
        saved = SavedQuery(
            user_id=current_user.id,
            question=payload.question,
            sql=exc.sql or "",
            explanation=None,
            chart_spec=None,
            columns=[],
            row_count=0,
            status="error",
            error_message=str(exc),
        )
        db.add(saved)
        await db.commit()
        await db.refresh(saved)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    chart = await generate_chart_spec(payload.question, result["sql"], result["columns"], result["rows"])

    saved = SavedQuery(
        user_id=current_user.id,
        question=payload.question,
        sql=result["sql"],
        explanation=result["explanation"],
        chart_spec=chart.model_dump(),
        columns=result["columns"],
        row_count=len(result["rows"]),
        status="success",
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)

    return build_query_response(saved, rows=result["rows"])


@router.get("/queries", response_model=list[SavedQuerySummary])
async def list_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedQuery]:
    stmt = (
        select(SavedQuery)
        .where(SavedQuery.user_id == current_user.id)
        .order_by(SavedQuery.created_at.desc())
        .limit(100)
    )
    return list((await db.execute(stmt)).scalars().all())


async def _get_owned_query(query_id: uuid.UUID, current_user: User, db: AsyncSession) -> SavedQuery:
    stmt = select(SavedQuery).where(SavedQuery.id == query_id, SavedQuery.user_id == current_user.id)
    saved = (await db.execute(stmt)).scalars().first()
    if saved is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return saved


@router.post("/queries/{query_id}/rerun", response_model=QueryResponse)
async def rerun_query(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedQuery:
    saved = await _get_owned_query(query_id, current_user, db)
    if saved.status != "success":
        raise HTTPException(status_code=400, detail="Cannot re-run a query that previously failed")

    try:
        columns, rows = await execute_sql(saved.sql)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Re-running the saved query failed: {exc}") from exc

    return build_query_response(saved, rows=rows)


@router.delete("/queries/{query_id}", status_code=204)
async def delete_query(
    query_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    saved = await _get_owned_query(query_id, current_user, db)
    widgets = (
        await db.execute(select(DashboardWidget).where(DashboardWidget.saved_query_id == saved.id))
    ).scalars().all()
    for widget in widgets:
        await db.delete(widget)
    await db.delete(saved)
    await db.commit()
