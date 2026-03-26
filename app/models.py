from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.domain.campaign.status import CampaignStatus
from app.domain.sightings.enums import SightingWeather, TimeOfDay
from app.domain.users import UserRole, UserStatus
from app.time import utc_now
from app.utils import generate_uuid


def sql_enum_values(enum_type: type[StrEnum]) -> str:
    return ", ".join(f"'{value.value}'" for value in enum_type)


class AppUser(Base):
    __tablename__ = "app_users"
    __table_args__ = (
        CheckConstraint(
            f"role IN ({sql_enum_values(UserRole)})", name="chk_app_users_role"
        ),
        CheckConstraint(
            f"status IN ({sql_enum_values(UserStatus)})", name="chk_app_users_status"
        ),
        CheckConstraint(
            "trim(display_name) <> ''", name="chk_app_users_display_name_nonempty"
        ),
        CheckConstraint("trim(email) <> ''", name="chk_app_users_email_nonempty"),
        CheckConstraint(
            "display_name_normalized = lower(trim(display_name))",
            name="chk_app_users_display_name_normalized",
        ),
        CheckConstraint(
            "email_normalized = lower(trim(email))",
            name="chk_app_users_email_normalized",
        ),
        Index("idx_app_users_email_norm", "email_normalized", unique=True),
        Index("idx_app_users_role_name", "role", "display_name_normalized"),
    )

    role: Mapped[str] = mapped_column(String(20))
    display_name: Mapped[str] = mapped_column(String(128))
    display_name_normalized: Mapped[str] = mapped_column(String(128), unique=True)
    email: Mapped[str] = mapped_column(String(256))
    email_normalized: Mapped[str] = mapped_column(String(256))
    id: Mapped[str] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=generate_uuid,
        insert_default=generate_uuid,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        init=False,
        default=UserStatus.ACTIVE.value,
        insert_default=UserStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=utc_now,
        insert_default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=utc_now,
        insert_default=utc_now,
    )


class Trainer(Base):
    """Profile extension for users with role='trainer'."""

    __tablename__ = "trainers"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("app_users.id", ondelete="RESTRICT"), primary_key=True
    )


class Ranger(Base):
    """Profile extension for users with role='ranger'. Adds specialization."""

    __tablename__ = "rangers"
    __table_args__ = (
        CheckConstraint(
            "trim(specialization) <> ''", name="chk_rangers_specialization_nonempty"
        ),
        Index("idx_rangers_specialization", "specialization"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("app_users.id", ondelete="RESTRICT"), primary_key=True
    )
    specialization: Mapped[str] = mapped_column(String(50))


class Pokemon(Base):
    __tablename__ = "pokemon"
    __table_args__ = (
        CheckConstraint("trim(name) <> ''", name="chk_pokemon_name_nonempty"),
        CheckConstraint("trim(type1) <> ''", name="chk_pokemon_type1_nonempty"),
        CheckConstraint(
            "capture_rate >= 0 AND capture_rate <= 255",
            name="chk_pokemon_capture_rate_range",
        ),
        CheckConstraint(
            "generation >= 1 AND generation <= 4", name="chk_pokemon_generation_range"
        ),
        CheckConstraint(
            "type2 IS NULL OR trim(type2) <> ''", name="chk_pokemon_type2_nonempty"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    type1: Mapped[str]
    generation: Mapped[int]
    capture_rate: Mapped[int]
    is_legendary: Mapped[bool] = mapped_column(default=False)
    is_mythical: Mapped[bool] = mapped_column(default=False)
    is_baby: Mapped[bool] = mapped_column(default=False)
    type2: Mapped[str | None] = mapped_column(default=None)
    evolution_chain_id: Mapped[int | None] = mapped_column(default=None)


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint("trim(name) <> ''", name="chk_campaigns_name_nonempty"),
        CheckConstraint(
            "trim(description) <> ''", name="chk_campaigns_description_nonempty"
        ),
        CheckConstraint("trim(region) <> ''", name="chk_campaigns_region_nonempty"),
        CheckConstraint(
            f"status IN ({sql_enum_values(CampaignStatus)})",
            name="chk_campaigns_status",
        ),
        CheckConstraint(
            "end_date >= start_date", name="chk_campaigns_date_window_valid"
        ),
        Index("idx_campaigns_region_status", "region", "status"),
        Index("idx_campaigns_status_start_end", "status", "start_date", "end_date"),
    )

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date]
    end_date: Mapped[date]
    id: Mapped[str] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=generate_uuid,
        insert_default=generate_uuid,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=CampaignStatus.DRAFT.value,
        insert_default=CampaignStatus.DRAFT.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=utc_now,
        insert_default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=utc_now,
        insert_default=utc_now,
    )


class Sighting(Base):
    __tablename__ = "sightings"
    __table_args__ = (
        CheckConstraint(
            f"weather IN ({sql_enum_values(SightingWeather)})",
            name="chk_sightings_weather",
        ),
        CheckConstraint(
            f"time_of_day IN ({sql_enum_values(TimeOfDay)})",
            name="chk_sightings_time_of_day",
        ),
        CheckConstraint("trim(region) <> ''", name="chk_sightings_region_nonempty"),
        CheckConstraint("trim(route) <> ''", name="chk_sightings_route_nonempty"),
        CheckConstraint("height > 0", name="chk_sightings_height_positive"),
        CheckConstraint("weight > 0", name="chk_sightings_weight_positive"),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="chk_sightings_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="chk_sightings_longitude_range",
        ),
        CheckConstraint(
            "notes IS NULL OR trim(notes) <> ''", name="chk_sightings_notes_nonempty"
        ),
        CheckConstraint(
            "(is_confirmed = 0 AND confirmed_by_ranger_id IS NULL "
            "AND confirmed_at IS NULL) OR "
            "(is_confirmed = 1 AND confirmed_by_ranger_id IS NOT NULL "
            "AND confirmed_at IS NOT NULL)",
            name="chk_sightings_confirmation_consistent",
        ),
        CheckConstraint(
            "confirmed_by_ranger_id IS NULL OR confirmed_by_ranger_id <> ranger_id",
            name="chk_sightings_no_self_confirmation",
        ),
        Index("idx_sightings_date_id_desc", "date", "id"),
        Index("idx_sightings_campaign_date_id", "campaign_id", "date", "id"),
        Index(
            "idx_sightings_confirmed_region_date_id",
            "is_confirmed",
            "region",
            "date",
            "id",
        ),
        Index("idx_sightings_region_date_id", "region", "date", "id"),
        Index("idx_sightings_pokemon_date_id", "pokemon_id", "date", "id"),
        Index("idx_sightings_ranger_date_id", "ranger_id", "date", "id"),
    )

    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    ranger_id: Mapped[str] = mapped_column(ForeignKey("rangers.user_id"))
    region: Mapped[str]
    route: Mapped[str]
    date: Mapped[datetime]
    weather: Mapped[str]
    time_of_day: Mapped[str]
    height: Mapped[float]
    weight: Mapped[float]
    campaign_id: Mapped[str | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="RESTRICT"),
        default=None,
    )
    is_shiny: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    is_confirmed: Mapped[bool] = mapped_column(default=False)
    confirmed_by_ranger_id: Mapped[str | None] = mapped_column(
        ForeignKey("rangers.user_id", ondelete="RESTRICT"),
        default=None,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(default=None)
    id: Mapped[str] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=generate_uuid,
        insert_default=generate_uuid,
    )
