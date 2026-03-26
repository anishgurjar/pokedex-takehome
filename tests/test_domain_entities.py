from datetime import UTC, date, datetime

import pytest
from app.domain.campaigns import (
    Campaign,
    CampaignLockedError,
    CampaignStatus,
    InactiveCampaignError,
    InvalidCampaignTransition,
)
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


class TestCampaignEntity:
    def test_transition_to_updates_status(self):
        campaign = make_campaign(status=CampaignStatus.DRAFT)

        campaign.transition_to(CampaignStatus.ACTIVE)

        assert campaign.status == CampaignStatus.ACTIVE

    def test_transition_to_rejects_backward_move(self):
        campaign = make_campaign(status=CampaignStatus.COMPLETED)

        with pytest.raises(InvalidCampaignTransition):
            campaign.transition_to(CampaignStatus.ACTIVE)

    def test_update_details_rejects_completed_campaign(self):
        campaign = make_campaign(status=CampaignStatus.COMPLETED)

        with pytest.raises(CampaignLockedError):
            campaign.update_details(name="Updated Name")

    def test_update_details_updates_fields_and_preserves_date_validation(self):
        campaign = make_campaign()

        campaign.update_details(
            name="Johto Migration Study",
            region="Johto",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
        )

        assert campaign.name == "Johto Migration Study"
        assert campaign.region == "Johto"
        assert campaign.start_date == date(2026, 3, 1)
        assert campaign.end_date == date(2026, 3, 31)


class TestSightingEntity:
    def test_new_sighting_has_real_id_at_creation(self):
        sighting = Sighting(
            id="real-id",
            pokemon_id=25,
            ranger_id="ranger-1",
            campaign_id=None,
        )

        assert sighting.id == "real-id"

    def test_assign_to_campaign_requires_active_campaign(self):
        sighting = make_sighting()
        draft_campaign = make_campaign(status=CampaignStatus.DRAFT)

        with pytest.raises(InactiveCampaignError):
            sighting.assign_to_campaign(draft_campaign)

    def test_assign_to_campaign_sets_campaign_id(self):
        sighting = make_sighting()
        active_campaign = make_campaign(status=CampaignStatus.ACTIVE)

        sighting.assign_to_campaign(active_campaign)

        assert sighting.campaign_id == active_campaign.id

    def test_assert_deletable_rejects_locked_campaign(self):
        sighting = make_sighting()
        completed_campaign = make_campaign(status=CampaignStatus.COMPLETED)

        with pytest.raises(CampaignLockedError):
            sighting.assert_deletable(completed_campaign)
