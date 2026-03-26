from app.domain.campaign import Campaign, CampaignStatus
from app.domain.sightings import Sighting
from app.models import Campaign as CampaignRecord
from app.models import Sighting as SightingRecord
from app.repositories.campaigns import CampaignRepository
from app.repositories.sightings import SightingRepository
from app.schemas import SightingCreate
from app.utils import generate_uuid


class SightingCommandService:
    def __init__(
        self,
        sighting_repository: SightingRepository,
        campaign_repository: CampaignRepository,
    ):
        self.sighting_repository = sighting_repository
        self.campaign_repository = campaign_repository

    def create_sighting(
        self, sighting: SightingCreate, *, ranger_id: str
    ) -> SightingRecord:
        sighting_id = generate_uuid()
        sighting_entity = Sighting(
            id=sighting_id,
            pokemon_id=sighting.pokemon_id,
            ranger_id=ranger_id,
            campaign_id=None,
        )
        if sighting.campaign_id is not None:
            campaign = self.campaign_repository.get_by_id(sighting.campaign_id)
            if campaign is None:
                raise LookupError("Campaign not found")
            sighting_entity.assign_to_campaign(self._to_domain_campaign(campaign))
        return self.sighting_repository.create(
            sighting,
            sighting_id=sighting_entity.id,
            ranger_id=ranger_id,
        )

    def delete_sighting(self, sighting: SightingRecord) -> None:
        sighting_entity = Sighting(
            id=sighting.id,
            pokemon_id=sighting.pokemon_id,
            ranger_id=sighting.ranger_id,
            campaign_id=sighting.campaign_id,
        )
        if sighting.campaign_id is not None:
            campaign = self.campaign_repository.get_by_id(sighting.campaign_id)
            if campaign is not None:
                sighting_entity.assert_deletable(self._to_domain_campaign(campaign))
        self.sighting_repository.delete(sighting)

    @staticmethod
    def _to_domain_campaign(campaign: CampaignRecord) -> Campaign:
        return Campaign(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            region=campaign.region,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            status=CampaignStatus(campaign.status),
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
