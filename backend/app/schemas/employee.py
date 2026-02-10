from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.employee import EmployeeState


class EmployeeCreate(BaseModel):
    name: str
    email: str


class EmployeeRead(BaseModel):
    id: UUID
    name: str
    email: str
    current_state: EmployeeState
    created_at: datetime

    model_config = {"from_attributes": True}


class StateChangeRequest(BaseModel):
    new_state: EmployeeState


class StateLogRead(BaseModel):
    id: UUID
    state: EmployeeState
    entered_at: datetime
    exited_at: datetime | None

    model_config = {"from_attributes": True}


class TaskAssignRequest(BaseModel):
    source_id: UUID
    record_id: str


class TaskLogRead(BaseModel):
    id: UUID
    employee_id: UUID
    source_id: UUID
    record_id: str
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AHTMetric(BaseModel):
    employee_id: UUID
    employee_name: str
    source_id: UUID | None = None
    project_name: str | None = None
    average_handle_time_seconds: float
    task_count: int
