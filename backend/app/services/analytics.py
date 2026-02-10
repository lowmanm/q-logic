"""Analytics: team-wide metrics, occupancy, and leaderboard."""

from uuid import UUID

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, EmployeeState, TaskLog
from app.models.queue import RecordQueue, RecordStatus


async def get_team_aht(
    db: AsyncSession, source_id: UUID | None = None
) -> dict:
    """Average Handle Time across all employees."""
    stmt = select(
        func.avg(
            extract("epoch", TaskLog.completed_at) - extract("epoch", TaskLog.started_at)
        ).label("avg_seconds"),
        func.count(TaskLog.id).label("task_count"),
    ).where(TaskLog.completed_at.isnot(None))

    if source_id:
        stmt = stmt.where(TaskLog.source_id == source_id)

    result = await db.execute(stmt)
    row = result.one()
    return {
        "average_handle_time_seconds": float(row.avg_seconds or 0),
        "task_count": int(row.task_count or 0),
    }


async def get_agent_state_distribution(db: AsyncSession) -> dict:
    """Count of employees in each state."""
    stmt = (
        select(Employee.current_state, func.count(Employee.id).label("count"))
        .group_by(Employee.current_state)
    )
    result = await db.execute(stmt)
    dist = {state.value: 0 for state in EmployeeState}
    for row in result.all():
        dist[row.current_state.value] = row.count
    dist["total"] = sum(dist.values())
    return dist


async def get_leaderboard(
    db: AsyncSession, source_id: UUID | None = None
) -> list[dict]:
    """Per-employee AHT + task count, ranked by task count descending."""
    stmt = (
        select(
            Employee.id,
            Employee.name,
            Employee.current_state,
            func.count(TaskLog.id).label("task_count"),
            func.avg(
                extract("epoch", TaskLog.completed_at)
                - extract("epoch", TaskLog.started_at)
            ).label("avg_seconds"),
        )
        .outerjoin(
            TaskLog,
            (TaskLog.employee_id == Employee.id) & (TaskLog.completed_at.isnot(None)),
        )
    )

    if source_id:
        stmt = stmt.where(TaskLog.source_id == source_id)

    stmt = stmt.group_by(Employee.id, Employee.name, Employee.current_state).order_by(
        func.count(TaskLog.id).desc()
    )

    result = await db.execute(stmt)
    return [
        {
            "employee_id": str(row.id),
            "name": row.name,
            "current_state": row.current_state.value,
            "task_count": int(row.task_count or 0),
            "average_handle_time_seconds": float(row.avg_seconds or 0),
        }
        for row in result.all()
    ]


async def get_all_queue_stats(db: AsyncSession) -> list[dict]:
    """Queue stats for every provisioned project."""
    from app.models.registry import SourceMetadata

    stmt = (
        select(
            SourceMetadata.id,
            SourceMetadata.project_name,
            RecordQueue.status,
            func.count(RecordQueue.id).label("count"),
        )
        .outerjoin(RecordQueue, RecordQueue.source_id == SourceMetadata.id)
        .group_by(SourceMetadata.id, SourceMetadata.project_name, RecordQueue.status)
    )

    result = await db.execute(stmt)
    projects: dict[str, dict] = {}
    for row in result.all():
        pid = str(row.id)
        if pid not in projects:
            projects[pid] = {
                "source_id": pid,
                "project_name": row.project_name,
                "pending": 0,
                "assigned": 0,
                "completed": 0,
                "skipped": 0,
                "total": 0,
            }
        if row.status is not None:
            projects[pid][row.status.value] = row.count
            projects[pid]["total"] += row.count

    return list(projects.values())
