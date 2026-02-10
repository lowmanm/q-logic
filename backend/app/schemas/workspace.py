from uuid import UUID

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    source_id: UUID
    project_name: str
    table_name: str
    screen_pop_url_template: str | None
    columns: list[dict]  # [{physical_name, display_name, data_type, is_unique_id}]

    model_config = {"from_attributes": True}


class TaskRecord(BaseModel):
    """A single record from a dynamic project table, with screen pop URL resolved."""
    record: dict
    screen_pop_url: str | None = None


class EnqueueResponse(BaseModel):
    source_id: UUID
    records_enqueued: int


class QueueStatsResponse(BaseModel):
    source_id: UUID
    pending: int
    assigned: int
    completed: int
    skipped: int
    total: int


class NextTaskResponse(BaseModel):
    queue_id: UUID
    source_id: UUID
    record_id: int
    record: dict
    screen_pop_url: str | None = None
    queue_depth: int


class QueueActionResponse(BaseModel):
    queue_id: UUID
    status: str
