"""initial

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("google_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("picture", sa.String(500), nullable=True),
        sa.Column("list_slug", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_list_slug", "users", ["list_slug"], unique=True)

    sa.Enum("AVAILABLE", "RESERVED", "BOUGHT", name="giftstatus").create(op.get_bind())

    op.create_table(
        "gifts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("link", sa.String(1000), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.Enum("AVAILABLE", "RESERVED", "BOUGHT", name="giftstatus"), nullable=False, server_default="AVAILABLE"),
        sa.Column("claimed_by_name", sa.String(255), nullable=True),
        sa.Column("claimed_by_visitor_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("gifts")
    op.drop_table("users")
    sa.Enum("AVAILABLE", "RESERVED", "BOUGHT", name="giftstatus").drop(op.get_bind())
