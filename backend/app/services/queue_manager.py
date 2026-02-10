"""Queue Manager: enqueue records, pull next task, complete/skip with locking."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, text, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queue import RecordQueue, RecordStatus
from app.models.registry import SourceMetadata


async def enqueue_records(
    db: AsyncSession,
    source: SourceMetadata,
) -> int:
    """Bulk-insert one queue entry per row in the dynamic table.

    Only inserts rows that are not already queued (idempotent).
    Returns the number of new queue entries created.
    """
    table_name = source.table_name

    # Get IDs already queued for this source
    existing = select(RecordQueue.record_id).where(
        RecordQueue.source_id == source.id
    )
    existing_result = await db.execute(existing)
    existing_ids = {row[0] for row in existing_result.all()}

    # Get all record IDs from the dynamic table
    rows_result = await db.execute(text(f'SELECT id FROM "{table_name}" ORDER BY id'))
    all_ids = [row[0] for row in rows_result.all()]

    new_entries = []
    for record_id in all_ids:
        if record_id not in existing_ids:
            new_entries.append(
                RecordQueue(
                    source_id=source.id,
                    record_id=record_id,
                    status=RecordStatus.PENDING,
                    priority=0,
                )
            )

    db.add_all(new_entries)
    await db.commit()
    return len(new_entries)


async def get_next_record(
    db: AsyncSession,
    source_id: UUID,
    employee_id: UUID,
) -> RecordQueue | None:
    """Atomically reserve the next pending record for an employee.

    Uses FOR UPDATE SKIP LOCKED to prevent two agents from receiving
    the same record.  Returns None if the queue is empty.
    """
    stmt = (
        select(RecordQueue)
        .where(
            RecordQueue.source_id == source_id,
            RecordQueue.status == RecordStatus.PENDING,
        )
        .order_by(RecordQueue.priority.desc(), RecordQueue.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )

    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        return None

    now = datetime.now(timezone.utc)
    entry.status = RecordStatus.ASSIGNED
    entry.assigned_to = employee_id
    entry.assigned_at = now
    await db.commit()
    await db.refresh(entry)
    return entry


async def complete_record(db: AsyncSession, queue_id: UUID) -> RecordQueue:
    """Mark a queue entry as completed."""
    entry = await db.get(RecordQueue, queue_id)
    if entry is None:
        raise ValueError(f"Queue entry {queue_id} not found")
    entry.status = RecordStatus.COMPLETED
    entry.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(entry)
    return entry


async def skip_record(db: AsyncSession, queue_id: UUID) -> RecordQueue:
    """Mark a queue entry as skipped and release it."""
    entry = await db.get(RecordQueue, queue_id)
    if entry is None:
        raise ValueError(f"Queue entry {queue_id} not found")
    entry.status = RecordStatus.SKIPPED
    entry.assigned_to = None
    entry.assigned_at = None
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_queue_stats(
    db: AsyncSession, source_id: UUID
) -> dict:
    """Return counts of records by status for a project's queue."""
    stmt = (
        select(
            RecordQueue.status,
            func.count(RecordQueue.id).label("count"),
        )
        .where(RecordQueue.source_id == source_id)
        .group_by(RecordQueue.status)
    )
    result = await db.execute(stmt)
    stats = {status.value: 0 for status in RecordStatus}
    for row in result.all():
        stats[row.status.value] = row.count
    stats["total"] = sum(stats.values())
    return stats


async def get_queue_depth(db: AsyncSession, source_id: UUID) -> int:
    """Return the number of pending records in the queue."""
    stmt = (
        select(func.count(RecordQueue.id))
        .where(
            RecordQueue.source_id == source_id,
            RecordQueue.status == RecordStatus.PENDING,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()
