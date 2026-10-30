from app.models.saved_query import SavedQuery
from app.schemas.query import ChartSpec, QueryResponse


def build_query_response(saved: SavedQuery, rows: list[dict]) -> QueryResponse:
    chart = ChartSpec(**saved.chart_spec) if saved.chart_spec else None
    return QueryResponse(
        id=saved.id,
        question=saved.question,
        sql=saved.sql,
        explanation=saved.explanation,
        columns=saved.columns or [],
        rows=rows,
        row_count=len(rows),
        chart_spec=chart,
        status=saved.status,
        error_message=saved.error_message,
        created_at=saved.created_at,
    )
