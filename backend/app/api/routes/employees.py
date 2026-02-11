"""Routes for employee tracking, state management, and AHT metrics."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, Role, get_current_user, require_role
from app.core.database import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    StateChangeRequest,
    TaskAssignRequest,
    TaskLogRead,
    AHTMetric,
)
from app.services.employee import (
    create_employee,
    get_employee,
    list_employees,
    change_state,
    assign_task,
    complete_task,
    get_aht,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeRead)
async def create(
    body: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
):
    """Register a new employee. Admin/Supervisor only."""
    emp = await create_employee(db, name=body.name, email=body.email)
    return emp


@router.get("", response_model=list[EmployeeRead])
async def list_all(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List all employees."""
    return await list_employees(db)


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_one(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single employee by ID."""
    emp = await get_employee(db, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return emp


@router.put("/{employee_id}/state", response_model=EmployeeRead)
async def update_state(
    employee_id: UUID,
    body: StateChangeRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Change an employee's state (Available, In-Task, Break, Wrap-up)."""
    try:
        emp = await change_state(db, employee_id, body.new_state)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return emp


@router.post("/{employee_id}/tasks", response_model=TaskLogRead)
async def create_task(
    employee_id: UUID,
    body: TaskAssignRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Assign a task to an employee (auto-transitions to IN_TASK)."""
    try:
        task = await assign_task(db, employee_id, body.source_id, body.record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return task


@router.post("/tasks/{task_id}/complete", response_model=TaskLogRead)
async def finish_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Mark a task as completed (auto-transitions employee to WRAP_UP)."""
    try:
        task = await complete_task(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return task


@router.get("/{employee_id}/metrics/aht", response_model=AHTMetric)
async def get_employee_aht(
    employee_id: UUID,
    source_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get Average Handle Time for an employee, optionally filtered by project."""
    try:
        return await get_aht(db, employee_id, source_id=source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
