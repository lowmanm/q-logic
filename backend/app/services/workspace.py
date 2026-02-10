"""Agent Workspace: dynamic data loading and screen pop URL injection."""

from uuid import UUID

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.registry import SourceMetadata, ColumnMetadata


async def get_project_info(db: AsyncSession, source_id: UUID) -> SourceMetadata | None:
    stmt = (
        select(SourceMetadata)
        .options(selectinload(SourceMetadata.columns))
        .where(SourceMetadata.id == source_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_projects(db: AsyncSession) -> list[SourceMetadata]:
    stmt = select(SourceMetadata).options(selectinload(SourceMetadata.columns))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def fetch_records(
    db: AsyncSession,
    source: SourceMetadata,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Fetch rows from the dynamic table for a given project."""
    table_name = source.table_name
    query = text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset')
    result = await db.execute(query, {"limit": limit, "offset": offset})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def fetch_record_by_id(
    db: AsyncSession,
    source: SourceMetadata,
    record_id: int,
) -> dict | None:
    """Fetch a single row from a dynamic table by its id."""
    table_name = source.table_name
    query = text(f'SELECT * FROM "{table_name}" WHERE id = :record_id')
    result = await db.execute(query, {"record_id": record_id})
    row = result.mappings().first()
    return dict(row) if row else None


def resolve_screen_pop_url(
    source: SourceMetadata, record: dict
) -> str | None:
    """Inject the unique ID column value into the screen pop URL template."""
    if not source.screen_pop_url_template:
        return None

    # Find the column flagged as unique ID
    unique_col: ColumnMetadata | None = None
    for col in source.columns:
        if col.is_unique_id:
            unique_col = col
            break

    if not unique_col:
        return None

    value = record.get(unique_col.physical_name, "")
    return source.screen_pop_url_template.replace("{unique_id}", str(value))
