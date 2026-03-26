import pytest
from app.domain.campaign import (
    CampaignLockedError,
    CampaignStatus,
    InactiveCampaignError,
)
from app.domain.sightings import Sighting
from tests.domain.conftest import make_campaign, make_sighting


class TestSighting:
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
