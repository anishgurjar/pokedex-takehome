from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError


def _create_ranger(db_session, *, name: str, email: str, specialization: str) -> str:
    from app.models import AppUser, Ranger

    user = AppUser(
        role="ranger",
        display_name=name,
        display_name_normalized=name.strip().lower(),
        email=email,
        email_normalized=email.strip().lower(),
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(Ranger(user_id=user.id, specialization=specialization))
    db_session.commit()
    return user.id


class TestSightingConfirmationDatabaseConstraints:
    def test_db_rejects_self_confirmation(self, db_session, sample_pokemon):
        from app.models import Sighting

        ranger_id = _create_ranger(
            db_session,
            name="Ranger Ash",
            email="ash@pokemon-institute.org",
            specialization="Electric",
        )

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=ranger_id,
                region="Kanto",
                route="Route 1",
                date=datetime(2026, 3, 26, 10, 0, tzinfo=UTC),
                weather="sunny",
                time_of_day="day",
                height=0.4,
                weight=6.0,
                is_confirmed=True,
                confirmed_by_ranger_id=ranger_id,
                confirmed_at=datetime(2026, 3, 26, 11, 0, tzinfo=UTC),
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_incomplete_confirmation_metadata(
        self, db_session, sample_pokemon
    ):
        from app.models import Sighting

        reporter_id = _create_ranger(
            db_session,
            name="Ranger Ash",
            email="ash@pokemon-institute.org",
            specialization="Electric",
        )

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=reporter_id,
                region="Kanto",
                route="Route 1",
                date=datetime(2026, 3, 26, 10, 0, tzinfo=UTC),
                weather="sunny",
                time_of_day="day",
                height=0.4,
                weight=6.0,
                is_confirmed=True,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()
