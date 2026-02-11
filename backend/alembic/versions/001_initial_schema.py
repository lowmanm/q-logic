"""Initial schema: registry, employees, queue, users.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- source_metadata ---
    op.create_table(
        "source_metadata",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_name", sa.String(255), unique=True, nullable=False),
        sa.Column("table_name", sa.String(63), unique=True, nullable=False),
        sa.Column("screen_pop_url_template", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- column_metadata ---
    op.create_table(
        "column_metadata",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("source_metadata.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("physical_name", sa.String(63), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("is_unique_id", sa.Boolean, default=False),
    )
    op.create_index("ix_column_metadata_source_id", "column_metadata", ["source_id"])

    # --- users (auth) ---
    user_role = sa.Enum("admin", "supervisor", "agent", name="role")
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, default="agent", nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_role", "users", ["role"])

    # --- employees ---
    employee_state = sa.Enum(
        "available", "in_task", "break", "wrap_up", name="employeestate"
    )
    op.create_table(
        "employees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("current_state", employee_state, default="available"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_employees_current_state", "employees", ["current_state"])

    # --- employee_state_logs ---
    op.create_table(
        "employee_state_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", employee_state, nullable=False),
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_employee_state_logs_employee_id", "employee_state_logs", ["employee_id"]
    )

    # --- task_logs ---
    op.create_table(
        "task_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("source_metadata.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_id", sa.String(255), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_task_logs_employee_id", "task_logs", ["employee_id"])
    op.create_index("ix_task_logs_source_id", "task_logs", ["source_id"])
    op.create_index("ix_task_logs_completed_at", "task_logs", ["completed_at"])

    # --- record_queue ---
    record_status = sa.Enum(
        "pending", "assigned", "completed", "skipped", name="recordstatus"
    )
    op.create_table(
        "record_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("source_metadata.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_id", sa.BigInteger, nullable=False),
        sa.Column("status", record_status, default="pending", nullable=False),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column(
            "assigned_to",
            UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_record_queue_source_status", "record_queue", ["source_id", "status"]
    )
    op.create_index("ix_record_queue_assigned_to", "record_queue", ["assigned_to"])
    op.create_index(
        "ix_record_queue_source_record",
        "record_queue",
        ["source_id", "record_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("record_queue")
    op.drop_table("task_logs")
    op.drop_table("employee_state_logs")
    op.drop_table("employees")
    op.drop_table("column_metadata")
    op.drop_table("users")
    op.drop_table("source_metadata")
    op.execute("DROP TYPE IF EXISTS recordstatus")
    op.execute("DROP TYPE IF EXISTS employeestate")
    op.execute("DROP TYPE IF EXISTS role")
