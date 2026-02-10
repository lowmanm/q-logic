"""Employee tracking: state engine and AHT metrics."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee, EmployeeState, EmployeeStateLog, TaskLog
from app.schemas.employee import AHTMetric


async def create_employee(db: AsyncSession, name: str, email: str) -> Employee:
    emp = Employee(name=name, email=email, current_state=EmployeeState.AVAILABLE)
    db.add(emp)
    # Create initial state log
    log = EmployeeStateLog(employee_id=emp.id, state=EmployeeState.AVAILABLE)
    db.add(log)
    await db.commit()
    await db.refresh(emp)
    return emp


async def get_employee(db: AsyncSession, employee_id: UUID) -> Employee | None:
    return await db.get(Employee, employee_id)


async def list_employees(db: AsyncSession) -> list[Employee]:
    result = await db.execute(select(Employee))
    return list(result.scalars().all())


async def change_state(
    db: AsyncSession, employee_id: UUID, new_state: EmployeeState
) -> Employee:
    emp = await db.get(Employee, employee_id)
    if emp is None:
        raise ValueError(f"Employee {employee_id} not found")

    now = datetime.now(timezone.utc)

    # Close the current open state log
    stmt = (
        select(EmployeeStateLog)
        .where(
            EmployeeStateLog.employee_id == employee_id,
            EmployeeStateLog.exited_at.is_(None),
        )
        .order_by(EmployeeStateLog.entered_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    current_log = result.scalar_one_or_none()
    if current_log:
        current_log.exited_at = now

    # Open a new state log
    new_log = EmployeeStateLog(
        employee_id=employee_id, state=new_state, entered_at=now
    )
    db.add(new_log)

    emp.current_state = new_state
    await db.commit()
    await db.refresh(emp)
    return emp


async def assign_task(
    db: AsyncSession, employee_id: UUID, source_id: UUID, record_id: str
) -> TaskLog:
    """Assign a task to an employee and transition them to IN_TASK."""
    emp = await db.get(Employee, employee_id)
    if emp is None:
        raise ValueError(f"Employee {employee_id} not found")

    task = TaskLog(
        employee_id=employee_id, source_id=source_id, record_id=record_id
    )
    db.add(task)

    # Auto-transition to IN_TASK
    if emp.current_state != EmployeeState.IN_TASK:
        await change_state(db, employee_id, EmployeeState.IN_TASK)

    await db.commit()
    await db.refresh(task)
    return task


async def complete_task(db: AsyncSession, task_id: UUID) -> TaskLog:
    """Mark a task as completed and transition employee to WRAP_UP."""
    task = await db.get(TaskLog, task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    task.completed_at = datetime.now(timezone.utc)

    # Transition employee to WRAP_UP
    await change_state(db, task.employee_id, EmployeeState.WRAP_UP)

    await db.commit()
    await db.refresh(task)
    return task


async def get_aht(
    db: AsyncSession, employee_id: UUID, source_id: UUID | None = None
) -> AHTMetric:
    """Calculate Average Handle Time for an employee, optionally filtered by project."""
    emp = await db.get(Employee, employee_id)
    if emp is None:
        raise ValueError(f"Employee {employee_id} not found")

    stmt = select(
        func.avg(
            extract("epoch", TaskLog.completed_at) - extract("epoch", TaskLog.started_at)
        ).label("avg_seconds"),
        func.count(TaskLog.id).label("task_count"),
    ).where(
        TaskLog.employee_id == employee_id,
        TaskLog.completed_at.isnot(None),
    )

    if source_id:
        stmt = stmt.where(TaskLog.source_id == source_id)

    result = await db.execute(stmt)
    row = result.one()

    return AHTMetric(
        employee_id=employee_id,
        employee_name=emp.name,
        source_id=source_id,
        average_handle_time_seconds=float(row.avg_seconds or 0),
        task_count=int(row.task_count or 0),
    )
