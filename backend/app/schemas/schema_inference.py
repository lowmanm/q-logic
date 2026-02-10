from pydantic import BaseModel


class InferredColumn(BaseModel):
    original_name: str
    inferred_type: str  # STRING, INTEGER, FLOAT, BOOLEAN, DATE
    suggested_display_name: str
    is_primary_key_candidate: bool


class SchemaInferenceResponse(BaseModel):
    filename: str
    row_count: int
    columns: list[InferredColumn]


class FinalizedColumn(BaseModel):
    original_name: str
    display_name: str
    data_type: str  # STRING, INTEGER, FLOAT, BOOLEAN, DATE
    is_unique_id: bool = False


class ProvisionRequest(BaseModel):
    project_name: str
    screen_pop_url_template: str | None = None
    columns: list[FinalizedColumn]


class ProvisionResponse(BaseModel):
    project_name: str
    table_name: str
    source_id: str
    column_count: int
