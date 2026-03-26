from app.domain.campaigns import Campaign, CampaignStatus
from app.models import Campaign as CampaignRecord
from app.repositories.campaigns import CampaignRepository
from app.schemas import (
    CampaignCreate,
    CampaignSummaryResponse,
    CampaignTransitionRequest,
    CampaignUpdate,
)
from app.utils import generate_uuid


class CampaignService:
    def __init__(self, repository: CampaignRepository):
        self.repository = repository

    def create_campaign(self, payload: CampaignCreate) -> CampaignRecord:
        campaign_entity = Campaign.create(
            id=generate_uuid(),
            name=payload.name,
            description=payload.description,
            region=payload.region,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        campaign = CampaignRecord(
            name=campaign_entity.name,
            description=campaign_entity.description,
            region=campaign_entity.region,
            start_date=campaign_entity.start_date,
            end_date=campaign_entity.end_date,
            status=campaign_entity.status.value,
        )
        campaign.id = campaign_entity.id
        campaign.created_at = campaign_entity.created_at
        campaign.updated_at = campaign_entity.updated_at
        return self.repository.create(campaign)

    def update_campaign(
        self, campaign: CampaignRecord, payload: CampaignUpdate
    ) -> CampaignRecord:
        campaign_entity = self._to_domain_entity(campaign)
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return campaign
        campaign_entity.update_details(**update_data)
        self._apply_domain_entity(campaign, campaign_entity)
        return self.repository.save(campaign)

    def transition_campaign(
        self, campaign: CampaignRecord, payload: CampaignTransitionRequest
    ) -> CampaignRecord:
        campaign_entity = self._to_domain_entity(campaign)
        campaign_entity.transition_to(CampaignStatus(payload.to_status))
        self._apply_domain_entity(campaign, campaign_entity)
        return self.repository.save(campaign)

    def get_summary(self, campaign: CampaignRecord) -> CampaignSummaryResponse:
        return self.repository.build_summary(campaign.id)

    @staticmethod
    def _to_domain_entity(campaign: CampaignRecord) -> Campaign:
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

    @staticmethod
    def _apply_domain_entity(campaign: CampaignRecord, entity: Campaign) -> None:
        campaign.name = entity.name
        campaign.description = entity.description
        campaign.region = entity.region
        campaign.start_date = entity.start_date
        campaign.end_date = entity.end_date
        campaign.status = entity.status.value
        campaign.updated_at = entity.updated_at
