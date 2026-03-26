from datetime import UTC, date, datetime

from app.domain.campaign import Campaign, CampaignStatus
from app.domain.sightings import Sighting


def make_campaign(*, status: CampaignStatus = CampaignStatus.DRAFT) -> Campaign:
    now = datetime(2026, 3, 26, 12, 0, tzinfo=UTC)
    return Campaign(
        id="campaign-1",
        name="Cerulean Cave Survey",
        description="Rare encounter survey",
        region="Kanto",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
        status=status,
        created_at=now,
        updated_at=now,
    )


def make_sighting() -> Sighting:
    return Sighting(
        id="sighting-1",
        pokemon_id=25,
        ranger_id="ranger-1",
        campaign_id=None,
    )
