"""Routes for the Agent Workspace: projects, records, queue, and screen pop."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.workspace import (
    ProjectInfo,
    TaskRecord,
    EnqueueResponse,
    QueueStatsResponse,
    NextTaskResponse,
    QueueActionResponse,
)
from app.services.workspace import (
    get_project_info,
    list_projects,
    fetch_records,
    fetch_record_by_id,
    resolve_screen_pop_url,
)
from app.services.queue_manager import (
    enqueue_records,
    get_next_record,
    complete_record,
    skip_record,
    get_queue_stats,
    get_queue_depth,
)

router = APIRouter(prefix="/workspace", tags=["Workspace"])


# ── Project CRUD ───────────────────────────────────────────────


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


# ── Raw record browsing (kept for admin use) ──────────────────


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


# ── Queue operations ───────────────────────────────────────────


@router.post("/projects/{source_id}/enqueue", response_model=EnqueueResponse)
async def enqueue_project(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Populate the work queue from all rows in the project table.

    Idempotent — rows already queued are skipped.
    """
    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    count = await enqueue_records(db, source)
    return EnqueueResponse(source_id=source_id, records_enqueued=count)


@router.get("/projects/{source_id}/queue-stats", response_model=QueueStatsResponse)
async def queue_stats(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get queue status counts for a project."""
    stats = await get_queue_stats(db, source_id)
    return QueueStatsResponse(
        source_id=source_id,
        pending=stats["pending"],
        assigned=stats["assigned"],
        completed=stats["completed"],
        skipped=stats["skipped"],
        total=stats["total"],
    )


@router.post("/projects/{source_id}/next", response_model=NextTaskResponse)
async def next_task(
    source_id: UUID,
    employee_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Pull the next pending record from the queue for an employee.

    Uses FOR UPDATE SKIP LOCKED to guarantee no two agents receive the
    same record.
    """
    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    entry = await get_next_record(db, source_id, employee_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Queue is empty — no pending records.")

    # Fetch the actual row data from the dynamic table
    row = await fetch_record_by_id(db, source, entry.record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found in table.")

    depth = await get_queue_depth(db, source_id)

    return NextTaskResponse(
        queue_id=entry.id,
        source_id=source_id,
        record_id=entry.record_id,
        record=row,
        screen_pop_url=resolve_screen_pop_url(source, row),
        queue_depth=depth,
    )


@router.post("/queue/{queue_id}/complete", response_model=QueueActionResponse)
async def complete_queue_item(
    queue_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark a queue entry as completed."""
    try:
        entry = await complete_record(db, queue_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QueueActionResponse(queue_id=entry.id, status=entry.status.value)


@router.post("/queue/{queue_id}/skip", response_model=QueueActionResponse)
async def skip_queue_item(
    queue_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Skip a queue entry (releases assignment)."""
    try:
        entry = await skip_record(db, queue_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QueueActionResponse(queue_id=entry.id, status=entry.status.value)
