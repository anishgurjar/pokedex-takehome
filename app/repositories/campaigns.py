from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import AppUser, Campaign, Sighting
from app.schemas import CampaignContributorResponse, CampaignSummaryResponse


@dataclass(frozen=True)
class CampaignSummaryStats:
    total_sightings: int
    unique_species_observed: int
    observation_started_at: object | None
    observation_ended_at: object | None


class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, campaign: Campaign) -> Campaign:
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def get_by_id(self, campaign_id: str) -> Campaign | None:
        return self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        ).scalar_one_or_none()

    def save(self, campaign: Campaign) -> Campaign:
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def summary_stats(self, campaign_id: str) -> CampaignSummaryStats:
        row = self.db.execute(
            select(
                func.count(Sighting.id),
                func.count(distinct(Sighting.pokemon_id)),
                func.min(Sighting.date),
                func.max(Sighting.date),
            ).where(Sighting.campaign_id == campaign_id)
        ).one()

        return CampaignSummaryStats(
            total_sightings=row[0] or 0,
            unique_species_observed=row[1] or 0,
            observation_started_at=row[2],
            observation_ended_at=row[3],
        )

    def contributing_rangers(
        self, campaign_id: str
    ) -> list[CampaignContributorResponse]:
        rows = self.db.execute(
            select(
                AppUser.id,
                AppUser.display_name,
                func.count(Sighting.id).label("sightings_count"),
            )
            .join(Sighting, Sighting.ranger_id == AppUser.id)
            .where(Sighting.campaign_id == campaign_id)
            .group_by(AppUser.id, AppUser.display_name)
            .order_by(func.count(Sighting.id).desc(), AppUser.display_name.asc())
        ).all()

        return [
            CampaignContributorResponse(
                id=row[0],
                name=row[1],
                sightings_count=row[2],
            )
            for row in rows
        ]

    def build_summary(self, campaign_id: str) -> CampaignSummaryResponse:
        stats = self.summary_stats(campaign_id)
        return CampaignSummaryResponse(
            campaign_id=campaign_id,
            total_sightings=stats.total_sightings,
            unique_species_observed=stats.unique_species_observed,
            contributing_rangers=self.contributing_rangers(campaign_id),
            observation_started_at=stats.observation_started_at,
            observation_ended_at=stats.observation_ended_at,
        )
