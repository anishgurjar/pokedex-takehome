"""add_domain_check_constraints

Revision ID: 9d2b8a6fb1c4
Revises: 970f2f7f9d0b

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d2b8a6fb1c4"
down_revision: str | Sequence[str] | None = "970f2f7f9d0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("app_users", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_app_users_display_name_nonempty", "trim(display_name) <> ''"
        )
        batch_op.create_check_constraint(
            "chk_app_users_email_nonempty", "trim(email) <> ''"
        )
        batch_op.create_check_constraint(
            "chk_app_users_display_name_normalized",
            "display_name_normalized = lower(trim(display_name))",
        )
        batch_op.create_check_constraint(
            "chk_app_users_email_normalized", "email_normalized = lower(trim(email))"
        )

    with op.batch_alter_table("rangers", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_rangers_specialization_nonempty", "trim(specialization) <> ''"
        )

    with op.batch_alter_table("pokemon", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_pokemon_name_nonempty", "trim(name) <> ''"
        )
        batch_op.create_check_constraint(
            "chk_pokemon_type1_nonempty", "trim(type1) <> ''"
        )
        batch_op.create_check_constraint(
            "chk_pokemon_capture_rate_range",
            "capture_rate >= 0 AND capture_rate <= 255",
        )
        batch_op.create_check_constraint(
            "chk_pokemon_generation_range", "generation >= 1 AND generation <= 4"
        )
        batch_op.create_check_constraint(
            "chk_pokemon_type2_nonempty", "type2 IS NULL OR trim(type2) <> ''"
        )

    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "chk_sightings_weather",
            "weather IN ('sunny', 'rainy', 'snowy', 'sandstorm', 'foggy', 'clear')",
        )
        batch_op.create_check_constraint(
            "chk_sightings_time_of_day",
            "time_of_day IN ('morning', 'day', 'night')",
        )
        batch_op.create_check_constraint(
            "chk_sightings_region_nonempty", "trim(region) <> ''"
        )
        batch_op.create_check_constraint(
            "chk_sightings_route_nonempty", "trim(route) <> ''"
        )
        batch_op.create_check_constraint("chk_sightings_height_positive", "height > 0")
        batch_op.create_check_constraint("chk_sightings_weight_positive", "weight > 0")
        batch_op.create_check_constraint(
            "chk_sightings_latitude_range",
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
        )
        batch_op.create_check_constraint(
            "chk_sightings_longitude_range",
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
        )
        batch_op.create_check_constraint(
            "chk_sightings_notes_nonempty", "notes IS NULL OR trim(notes) <> ''"
        )


def downgrade() -> None:
    with op.batch_alter_table("sightings", recreate="always") as batch_op:
        batch_op.drop_constraint("chk_sightings_notes_nonempty", type_="check")
        batch_op.drop_constraint("chk_sightings_longitude_range", type_="check")
        batch_op.drop_constraint("chk_sightings_latitude_range", type_="check")
        batch_op.drop_constraint("chk_sightings_weight_positive", type_="check")
        batch_op.drop_constraint("chk_sightings_height_positive", type_="check")
        batch_op.drop_constraint("chk_sightings_route_nonempty", type_="check")
        batch_op.drop_constraint("chk_sightings_region_nonempty", type_="check")
        batch_op.drop_constraint("chk_sightings_time_of_day", type_="check")
        batch_op.drop_constraint("chk_sightings_weather", type_="check")

    with op.batch_alter_table("pokemon", recreate="always") as batch_op:
        batch_op.drop_constraint("chk_pokemon_type2_nonempty", type_="check")
        batch_op.drop_constraint("chk_pokemon_generation_range", type_="check")
        batch_op.drop_constraint("chk_pokemon_capture_rate_range", type_="check")
        batch_op.drop_constraint("chk_pokemon_type1_nonempty", type_="check")
        batch_op.drop_constraint("chk_pokemon_name_nonempty", type_="check")

    with op.batch_alter_table("rangers", recreate="always") as batch_op:
        batch_op.drop_constraint("chk_rangers_specialization_nonempty", type_="check")

    with op.batch_alter_table("app_users", recreate="always") as batch_op:
        batch_op.drop_constraint("chk_app_users_email_normalized", type_="check")
        batch_op.drop_constraint("chk_app_users_display_name_normalized", type_="check")
        batch_op.drop_constraint("chk_app_users_email_nonempty", type_="check")
        batch_op.drop_constraint("chk_app_users_display_name_nonempty", type_="check")
