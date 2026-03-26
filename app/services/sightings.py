from app.domain.campaign import Campaign, CampaignLockedError, CampaignStatus
from app.domain.sightings import Sighting, SightingAlreadyConfirmedError
from app.models import Campaign as CampaignRecord
from app.models import Sighting as SightingRecord
from app.repositories.campaigns import CampaignRepository
from app.repositories.sightings import SightingRepository
from app.schemas import SightingConfirmationResponse, SightingCreate
from app.time import utc_now
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
            is_confirmed=sighting.is_confirmed,
            confirmed_by_ranger_id=sighting.confirmed_by_ranger_id,
            confirmed_at=sighting.confirmed_at,
        )
        if sighting.campaign_id is not None:
            campaign = self.campaign_repository.get_by_id(sighting.campaign_id)
            if campaign is not None:
                sighting_entity.assert_deletable(self._to_domain_campaign(campaign))
        self.sighting_repository.delete(sighting)

    def confirm_sighting(
        self, sighting_id: str, *, confirmed_by_ranger_id: str
    ) -> SightingConfirmationResponse:
        confirmer_name = self.sighting_repository.get_ranger_display_name(
            confirmed_by_ranger_id
        )
        if confirmer_name is None:
            raise PermissionError("Only registered rangers can confirm sightings")

        sighting = self.sighting_repository.get_raw_by_id(sighting_id)
        if sighting is None:
            raise LookupError("Sighting not found")

        sighting_entity = Sighting(
            id=sighting.id,
            pokemon_id=sighting.pokemon_id,
            ranger_id=sighting.ranger_id,
            campaign_id=sighting.campaign_id,
            is_confirmed=sighting.is_confirmed,
            confirmed_by_ranger_id=sighting.confirmed_by_ranger_id,
            confirmed_at=sighting.confirmed_at,
        )

        campaign = None
        if sighting.campaign_id is not None:
            campaign_record = self.campaign_repository.get_by_id(sighting.campaign_id)
            if campaign_record is None:
                raise LookupError("Campaign not found")
            campaign = self._to_domain_campaign(campaign_record)

        confirmed_at = utc_now()
        sighting_entity.confirm(
            confirmed_by_ranger_id=confirmed_by_ranger_id,
            confirmed_at=confirmed_at,
            campaign=campaign,
        )

        if not self.sighting_repository.mark_confirmed(
            sighting_id,
            confirmed_by_ranger_id=confirmed_by_ranger_id,
            confirmed_at=confirmed_at,
        ):
            current_sighting = self.sighting_repository.get_raw_by_id(sighting_id)
            if current_sighting is None:
                raise LookupError("Sighting not found")
            if current_sighting.is_confirmed:
                raise SightingAlreadyConfirmedError(
                    "Sighting has already been confirmed"
                )
            raise CampaignLockedError("Unable to confirm sighting")

        confirmation = self.sighting_repository.get_confirmation_by_sighting_id(
            sighting_id
        )
        if confirmation is None:
            raise LookupError("Sighting not found")
        return confirmation

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
