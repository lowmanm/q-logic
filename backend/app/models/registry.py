import uuid
from datetime import datetime

from sqlalchemy import Index, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceMetadata(Base):
    """Registry table mapping project names to their dynamically created tables."""

    __tablename__ = "source_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    screen_pop_url_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    columns: Mapped[list["ColumnMetadata"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class ColumnMetadata(Base):
    """Stores display name aliases and metadata for each column in a dynamic table."""

    __tablename__ = "column_metadata"
    __table_args__ = (
        Index("ix_column_metadata_source_id", "source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_metadata.id", ondelete="CASCADE")
    )
    physical_name: Mapped[str] = mapped_column(String(63), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_unique_id: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped["SourceMetadata"] = relationship(back_populates="columns")
