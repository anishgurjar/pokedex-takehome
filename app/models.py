from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import generate_uuid


class AppUser(Base):
    __tablename__ = "app_users"
    __table_args__ = (
        CheckConstraint("role IN ('trainer', 'ranger')", name="chk_app_users_role"),
        CheckConstraint(
            "status IN ('active', 'disabled')", name="chk_app_users_status"
        ),
        Index("idx_app_users_email_norm", "email_normalized"),
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
        default="active",
        insert_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=datetime.utcnow,
        insert_default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        default_factory=datetime.utcnow,
        insert_default=datetime.utcnow,
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
    __table_args__ = (Index("idx_rangers_specialization", "specialization"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("app_users.id", ondelete="RESTRICT"), primary_key=True
    )
    specialization: Mapped[str] = mapped_column(String(50))


class Pokemon(Base):
    __tablename__ = "pokemon"

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


class Sighting(Base):
    __tablename__ = "sightings"

    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    ranger_id: Mapped[str] = mapped_column(ForeignKey("rangers.user_id"))
    region: Mapped[str]
    route: Mapped[str]
    date: Mapped[datetime]
    weather: Mapped[str]
    time_of_day: Mapped[str]
    height: Mapped[float]
    weight: Mapped[float]
    is_shiny: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    is_confirmed: Mapped[bool] = mapped_column(default=False)
    id: Mapped[str] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=generate_uuid,
        insert_default=generate_uuid,
    )
