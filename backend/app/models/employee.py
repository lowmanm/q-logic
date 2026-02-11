import uuid
import enum
from datetime import datetime

from sqlalchemy import Index, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmployeeState(str, enum.Enum):
    AVAILABLE = "available"
    IN_TASK = "in_task"
    BREAK = "break"
    WRAP_UP = "wrap_up"


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_current_state", "current_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    current_state: Mapped[EmployeeState] = mapped_column(
        Enum(EmployeeState), default=EmployeeState.AVAILABLE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    state_logs: Mapped[list["EmployeeStateLog"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    task_logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )


class EmployeeStateLog(Base):
    __tablename__ = "employee_state_logs"
    __table_args__ = (
        Index("ix_employee_state_logs_employee_id", "employee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE")
    )
    state: Mapped[EmployeeState] = mapped_column(Enum(EmployeeState), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    exited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    employee: Mapped["Employee"] = relationship(back_populates="state_logs")


class TaskLog(Base):
    """Tracks individual task assignments against dynamic project tables."""

    __tablename__ = "task_logs"
    __table_args__ = (
        Index("ix_task_logs_employee_id", "employee_id"),
        Index("ix_task_logs_source_id", "source_id"),
        Index("ix_task_logs_completed_at", "completed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_metadata.id", ondelete="CASCADE")
    )
    record_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # row ID in the dynamic table
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    employee: Mapped["Employee"] = relationship(back_populates="task_logs")
