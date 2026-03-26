"""add_region_constraints_and_summary_indexes

Revision ID: 6a4f91b2c3d4
Revises: 3f1e2d4c5b6a

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a4f91b2c3d4"
down_revision: str | Sequence[str] | None = "3f1e2d4c5b6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


REGION_VALUES_SQL = "'Kanto', 'Johto', 'Hoenn', 'Sinnoh'"


def upgrade() -> None:
    with op.batch_alter_table("campaigns", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_campaigns_region",
            f"region IN ({REGION_VALUES_SQL})",
        )

    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_sightings_region",
            f"region IN ({REGION_VALUES_SQL})",
        )
        batch_op.create_index(
            "idx_sightings_region_is_confirmed",
            ["region", "is_confirmed"],
            unique=False,
        )
        batch_op.create_index(
            "idx_sightings_region_pokemon",
            ["region", "pokemon_id"],
            unique=False,
        )
        batch_op.create_index(
            "idx_sightings_region_ranger",
            ["region", "ranger_id"],
            unique=False,
        )
        batch_op.create_index(
            "idx_sightings_region_weather",
            ["region", "weather"],
            unique=False,
        )
        batch_op.create_index(
            "idx_sightings_region_time_of_day",
            ["region", "time_of_day"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.drop_index("idx_sightings_region_time_of_day")
        batch_op.drop_index("idx_sightings_region_weather")
        batch_op.drop_index("idx_sightings_region_ranger")
        batch_op.drop_index("idx_sightings_region_pokemon")
        batch_op.drop_index("idx_sightings_region_is_confirmed")
        batch_op.drop_constraint("chk_sightings_region", type_="check")

    with op.batch_alter_table("campaigns", recreate="always") as batch_op:
        batch_op.drop_constraint("chk_campaigns_region", type_="check")
