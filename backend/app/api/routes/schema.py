"""Routes for CSV schema inference and table provisioning."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.schema_inference import (
    SchemaInferenceResponse,
    ProvisionRequest,
    ProvisionResponse,
)
from app.services.inference import infer_schema
from app.services.provisioning import provision_table

router = APIRouter(prefix="/schema", tags=["Schema"])


@router.post("/infer", response_model=SchemaInferenceResponse)
async def infer_csv_schema(file: UploadFile = File(...)):
    """Upload a CSV file and get the inferred schema for each column."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    max_size = settings.MAX_CSV_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.MAX_CSV_SIZE_MB} MB.",
        )

    try:
        columns, row_count = infer_schema(content, max_rows=settings.CSV_SAMPLE_ROWS)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {e}")

    return SchemaInferenceResponse(
        filename=file.filename,
        row_count=row_count,
        columns=columns,
    )


@router.post("/provision", response_model=ProvisionResponse)
async def provision_project_table(
    request: ProvisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a dedicated PostgreSQL table from a finalized schema."""
    if not request.columns:
        raise HTTPException(status_code=400, detail="At least one column is required.")

    try:
        source = await provision_table(
            db,
            project_name=request.project_name,
            columns=request.columns,
            screen_pop_url_template=request.screen_pop_url_template,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {e}")

    return ProvisionResponse(
        project_name=source.project_name,
        table_name=source.table_name,
        source_id=str(source.id),
        column_count=len(source.columns),
    )
