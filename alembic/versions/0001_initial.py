"""initial schema: links + clicks

Revision ID: 0001
Revises:
Create Date: 2026-09-09

Note: indexes are created non-concurrently here because both tables are empty at
creation time. Any *later* index added to a populated table must use
op.create_index(..., postgresql_concurrently=True) in an autocommit block —
see decisions/0002 and the sqlalchemy-alembic skill's only-concurrent-indexes rule.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_custom", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("click_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_links_code", "links", ["code"], unique=True)

    op.create_table(
        "clicks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "link_id",
            sa.Integer(),
            sa.ForeignKey("links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_clicks_link_id", "clicks", ["link_id"])


def downgrade() -> None:
    op.drop_index("ix_clicks_link_id", table_name="clicks")
    op.drop_table("clicks")
    op.drop_index("ix_links_code", table_name="links")
    op.drop_table("links")
