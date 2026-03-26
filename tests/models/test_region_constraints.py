from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError


class TestRegionDatabaseConstraints:
    def test_db_rejects_invalid_sighting_region(
        self, db_session, sample_pokemon, sample_ranger
    ):
        from app.models import Sighting

        db_session.add(
            Sighting(
                pokemon_id=25,
                ranger_id=sample_ranger["id"],
                region="Orange Islands",
                route="Route 1",
                date=datetime(2026, 3, 26, 10, 0, tzinfo=UTC),
                weather="sunny",
                time_of_day="day",
                height=0.4,
                weight=6.0,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_invalid_campaign_region(self, db_session):
        from app.models import Campaign

        db_session.add(
            Campaign(
                name="Orange Islands Survey",
                description="Testing invalid region enforcement",
                region="Orange Islands",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 31),
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()
