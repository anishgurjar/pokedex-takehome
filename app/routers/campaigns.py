from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import CurrentPrincipal, require_role
from app.deps import get_db
from app.domain.campaign import CampaignDomainError, InvalidCampaignTransition
from app.repositories.campaigns import CampaignRepository
from app.schemas import (
    CampaignCreate,
    CampaignResponse,
    CampaignSummaryResponse,
    CampaignTransitionRequest,
    CampaignUpdate,
)
from app.services.campaigns import CampaignService

router = APIRouter(tags=["campaigns"])


def _get_campaign_or_404(campaign_id: str, repository: CampaignRepository):
    campaign = repository.get_by_id(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign(
    payload: CampaignCreate,
    _principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    service = CampaignService(CampaignRepository(db))
    return service.create_campaign(payload)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    repository = CampaignRepository(db)
    return _get_campaign_or_404(campaign_id, repository)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    _principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    repository = CampaignRepository(db)
    campaign = _get_campaign_or_404(campaign_id, repository)
    service = CampaignService(repository)
    try:
        return service.update_campaign(campaign, payload)
    except CampaignDomainError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/transition", response_model=CampaignResponse)
def transition_campaign(
    campaign_id: str,
    payload: CampaignTransitionRequest,
    _principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    repository = CampaignRepository(db)
    campaign = _get_campaign_or_404(campaign_id, repository)
    service = CampaignService(repository)
    try:
        return service.transition_campaign(campaign, payload)
    except InvalidCampaignTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/summary", response_model=CampaignSummaryResponse)
def get_campaign_summary(campaign_id: str, db: Session = Depends(get_db)):
    repository = CampaignRepository(db)
    campaign = _get_campaign_or_404(campaign_id, repository)
    service = CampaignService(repository)
    return service.get_summary(campaign)
