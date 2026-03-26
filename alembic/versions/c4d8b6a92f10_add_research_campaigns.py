"""add_research_campaigns

Revision ID: c4d8b6a92f10
Revises: 9d2b8a6fb1c4
Create Date: 2026-03-26 04:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d8b6a92f10"
down_revision: str | Sequence[str] | None = "9d2b8a6fb1c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("trim(name) <> ''", name="chk_campaigns_name_nonempty"),
        sa.CheckConstraint(
            "trim(description) <> ''", name="chk_campaigns_description_nonempty"
        ),
        sa.CheckConstraint("trim(region) <> ''", name="chk_campaigns_region_nonempty"),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'archived')",
            name="chk_campaigns_status",
        ),
        sa.CheckConstraint(
            "end_date >= start_date", name="chk_campaigns_date_window_valid"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_campaigns_region_status", "campaigns", ["region", "status"], unique=False
    )
    op.create_index(
        "idx_campaigns_status_start_end",
        "campaigns",
        ["status", "start_date", "end_date"],
        unique=False,
    )

    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("campaign_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_sightings_campaign_id_campaigns",
            "campaigns",
            ["campaign_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index(
            "idx_sightings_campaign_date_id",
            ["campaign_id", "date", "id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.drop_index("idx_sightings_campaign_date_id")
        batch_op.drop_constraint(
            "fk_sightings_campaign_id_campaigns", type_="foreignkey"
        )
        batch_op.drop_column("campaign_id")

    op.drop_index("idx_campaigns_status_start_end", table_name="campaigns")
    op.drop_index("idx_campaigns_region_status", table_name="campaigns")
    op.drop_table("campaigns")
