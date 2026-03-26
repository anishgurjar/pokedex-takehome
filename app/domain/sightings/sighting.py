from dataclasses import dataclass
from datetime import datetime

from app.domain.campaign import Campaign
from app.domain.sightings.errors import (
    SelfConfirmationError,
    SightingAlreadyConfirmedError,
)


@dataclass
class Sighting:
    id: str
    pokemon_id: int
    ranger_id: str
    campaign_id: str | None = None
    is_confirmed: bool = False
    confirmed_by_ranger_id: str | None = None
    confirmed_at: datetime | None = None

    def assign_to_campaign(self, campaign: Campaign) -> None:
        campaign.assert_accepts_sightings()
        self.campaign_id = campaign.id

    def assert_deletable(self, campaign: Campaign | None = None) -> None:
        if campaign is not None:
            campaign.assert_sightings_unlocked()

    def confirm(
        self,
        *,
        confirmed_by_ranger_id: str,
        confirmed_at: datetime,
        campaign: Campaign | None = None,
    ) -> None:
        if campaign is not None:
            campaign.assert_sightings_unlocked()
        if confirmed_by_ranger_id == self.ranger_id:
            raise SelfConfirmationError("Rangers cannot confirm their own sightings")
        if self.is_confirmed:
            raise SightingAlreadyConfirmedError("Sighting has already been confirmed")
        self.is_confirmed = True
        self.confirmed_by_ranger_id = confirmed_by_ranger_id
        self.confirmed_at = confirmed_at
