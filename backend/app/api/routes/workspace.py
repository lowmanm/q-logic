"""Routes for the Agent Workspace: project listing, record fetching, screen pop."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.workspace import ProjectInfo, TaskRecord
from app.services.workspace import (
    get_project_info,
    list_projects,
    fetch_records,
    fetch_record_by_id,
    resolve_screen_pop_url,
)

router = APIRouter(prefix="/workspace", tags=["Workspace"])


@router.get("/projects", response_model=list[ProjectInfo])
async def get_projects(db: AsyncSession = Depends(get_db)):
    """List all provisioned projects."""
    sources = await list_projects(db)
    return [
        ProjectInfo(
            source_id=s.id,
            project_name=s.project_name,
            table_name=s.table_name,
            screen_pop_url_template=s.screen_pop_url_template,
            columns=[
                {
                    "physical_name": c.physical_name,
                    "display_name": c.display_name,
                    "data_type": c.data_type,
                    "is_unique_id": c.is_unique_id,
                }
                for c in s.columns
            ],
        )
        for s in sources
    ]


@router.get("/projects/{source_id}", response_model=ProjectInfo)
async def get_project(source_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get details for a specific project."""
    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ProjectInfo(
        source_id=source.id,
        project_name=source.project_name,
        table_name=source.table_name,
        screen_pop_url_template=source.screen_pop_url_template,
        columns=[
            {
                "physical_name": c.physical_name,
                "display_name": c.display_name,
                "data_type": c.data_type,
                "is_unique_id": c.is_unique_id,
            }
            for c in source.columns
        ],
    )


@router.get("/projects/{source_id}/records", response_model=list[TaskRecord])
async def get_records(
    source_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Fetch records from a project's dynamic table."""
    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    rows = await fetch_records(db, source, limit=limit, offset=offset)
    return [
        TaskRecord(record=row, screen_pop_url=resolve_screen_pop_url(source, row))
        for row in rows
    ]


@router.get("/projects/{source_id}/records/{record_id}", response_model=TaskRecord)
async def get_record(
    source_id: UUID,
    record_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single record by ID with the screen pop URL resolved."""
    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    row = await fetch_record_by_id(db, source, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found.")

    return TaskRecord(record=row, screen_pop_url=resolve_screen_pop_url(source, row))
