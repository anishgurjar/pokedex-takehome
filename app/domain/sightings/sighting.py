from dataclasses import dataclass

from app.domain.campaign import Campaign


@dataclass
class Sighting:
    id: str
    pokemon_id: int
    ranger_id: str
    campaign_id: str | None = None

    def assign_to_campaign(self, campaign: Campaign) -> None:
        campaign.assert_accepts_sightings()
        self.campaign_id = campaign.id

    def assert_deletable(self, campaign: Campaign | None = None) -> None:
        if campaign is not None:
            campaign.assert_sightings_unlocked()
