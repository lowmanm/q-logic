import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecordStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RecordQueue(Base):
    """Work queue — one row per record that needs to be worked by an agent."""

    __tablename__ = "record_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_metadata.id", ondelete="CASCADE"),
        nullable=False,
    )
    record_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus), default=RecordStatus.PENDING, nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
