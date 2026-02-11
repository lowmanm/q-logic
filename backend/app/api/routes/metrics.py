"""Routes for the supervisor dashboard: team metrics, queue health, leaderboard."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, Role, require_role
from app.core.database import get_db
from app.services.analytics import (
    get_team_aht,
    get_agent_state_distribution,
    get_leaderboard,
    get_all_queue_stats,
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/team-aht")
async def team_aht(
    source_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
):
    """Team-wide Average Handle Time, optionally by project."""
    return await get_team_aht(db, source_id)


@router.get("/agent-states")
async def agent_states(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
):
    """Count of employees per state (Available, In-Task, Break, Wrap-up)."""
    return await get_agent_state_distribution(db)


@router.get("/leaderboard")
async def leaderboard(
    source_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
):
    """Per-employee metrics ranked by tasks completed."""
    return await get_leaderboard(db, source_id)


@router.get("/queue-stats")
async def all_queue_stats(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
):
    """Queue status breakdown for every provisioned project."""
    return await get_all_queue_stats(db)
