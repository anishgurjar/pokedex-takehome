from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError


class TestCampaignDatabaseConstraints:
    def test_db_rejects_campaign_with_end_before_start(self, db_session):
        from app.models import Campaign

        db_session.add(
            Campaign(
                name="Broken Campaign",
                description="Bad date ordering",
                region="Kanto",
                start_date=date.fromisoformat("2026-03-10"),
                end_date=date.fromisoformat("2026-03-01"),
                status="draft",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_db_rejects_invalid_campaign_status(self, db_session):
        from app.models import Campaign

        db_session.add(
            Campaign(
                name="Broken Campaign",
                description="Bad status",
                region="Kanto",
                start_date=date.fromisoformat("2026-03-01"),
                end_date=date.fromisoformat("2026-03-10"),
                status="paused",
            )
        )

        with pytest.raises(IntegrityError):
            db_session.commit()
