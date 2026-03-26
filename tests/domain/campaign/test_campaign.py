from datetime import date

import pytest
from app.domain.campaign import (
    CampaignLockedError,
    CampaignStatus,
    InvalidCampaignTransition,
)
from tests.domain.conftest import make_campaign


class TestCampaign:
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
