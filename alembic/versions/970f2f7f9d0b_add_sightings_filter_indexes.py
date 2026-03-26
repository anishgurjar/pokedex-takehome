"""add_sightings_filter_indexes

Revision ID: 970f2f7f9d0b
Revises: 7a60741dc732
Create Date: 2026-03-26 02:58:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "970f2f7f9d0b"
down_revision: str | Sequence[str] | None = "7a60741dc732"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_sightings_date_id_desc", "sightings", ["date", "id"], unique=False
    )
    op.create_index(
        "idx_sightings_region_date_id",
        "sightings",
        ["region", "date", "id"],
        unique=False,
    )
    op.create_index(
        "idx_sightings_pokemon_date_id",
        "sightings",
        ["pokemon_id", "date", "id"],
        unique=False,
    )
    op.create_index(
        "idx_sightings_ranger_date_id",
        "sightings",
        ["ranger_id", "date", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_sightings_ranger_date_id", table_name="sightings")
    op.drop_index("idx_sightings_pokemon_date_id", table_name="sightings")
    op.drop_index("idx_sightings_region_date_id", table_name="sightings")
    op.drop_index("idx_sightings_date_id_desc", table_name="sightings")
