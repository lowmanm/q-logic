"""Routes for CSV schema inference, table provisioning, and data loading."""

from uuid import UUID

import structlog
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.schema_inference import (
    SchemaInferenceResponse,
    ProvisionRequest,
    ProvisionResponse,
    DataLoadResponse,
)
from app.services.inference import infer_schema
from app.services.provisioning import provision_table
from app.services.data_loader import load_csv
from app.services.workspace import get_project_info

logger = structlog.get_logger("routes.schema")
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
    except Exception:
        logger.exception("csv_parse_failed", filename=file.filename)
        raise HTTPException(status_code=422, detail="Failed to parse CSV file.")

    logger.info("schema_inferred", filename=file.filename, columns=len(columns), rows=row_count)
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
    except Exception:
        logger.exception("provision_failed", project=request.project_name)
        raise HTTPException(status_code=500, detail="Table provisioning failed.")

    logger.info("table_provisioned", project=source.project_name, table=source.table_name)
    return ProvisionResponse(
        project_name=source.project_name,
        table_name=source.table_name,
        source_id=str(source.id),
        column_count=len(source.columns),
    )


@router.post("/{source_id}/load", response_model=DataLoadResponse)
async def load_csv_data(
    source_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Load CSV data into an already-provisioned project table.

    The CSV is streamed and inserted in batches.
    Rows that fail type conversion are skipped and reported.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    source = await get_project_info(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = await file.read()

    try:
        result = await load_csv(db, source, content)
    except Exception:
        logger.exception("data_load_failed", source_id=str(source_id))
        raise HTTPException(status_code=500, detail="Data load failed.")

    logger.info(
        "data_loaded",
        source_id=str(source_id),
        rows_loaded=result.rows_loaded,
        rows_failed=result.rows_failed,
    )
    return DataLoadResponse(
        source_id=str(source_id),
        rows_loaded=result.rows_loaded,
        rows_failed=result.rows_failed,
        errors=result.errors,
    )
