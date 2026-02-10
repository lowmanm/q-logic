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
