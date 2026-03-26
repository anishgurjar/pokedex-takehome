from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentPrincipal, require_role
from app.deps import get_db
from app.domain.campaign import CampaignLockedError, InactiveCampaignError
from app.repositories.campaigns import CampaignRepository
from app.repositories.errors import InvalidCursorError
from app.repositories.sightings import SightingRepository
from app.schemas import (
    MessageResponse,
    SightingCreate,
    SightingListParams,
    SightingListResponse,
    SightingResponse,
)
from app.services.sightings import SightingCommandService

router = APIRouter(tags=["sightings"])


def _get_sighting_list_params(
    params: Annotated[SightingListParams, Depends()],
) -> SightingListParams:
    if (
        params.date_from is not None
        and params.date_to is not None
        and params.date_from > params.date_to
    ):
        raise HTTPException(
            status_code=400,
            detail="date_from must be before or equal to date_to",
        )
    return params


@router.get("/sightings", response_model=SightingListResponse)
def list_sightings(
    params: Annotated[SightingListParams, Depends(_get_sighting_list_params)],
    db: Session = Depends(get_db),
):
    repository = SightingRepository(db)
    try:
        result = repository.list(params)
    except InvalidCursorError as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc
    return SightingListResponse(
        items=result.items,
        total_count=result.total_count,
        next_cursor=result.next_cursor,
    )


@router.post("/sightings", response_model=SightingResponse)
def create_sighting(
    sighting: SightingCreate,
    principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    repository = SightingRepository(db)
    if repository.get_pokemon_name(sighting.pokemon_id) is None:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    service = SightingCommandService(repository, CampaignRepository(db))
    try:
        new_sighting = service.create_sighting(sighting, ranger_id=principal.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Campaign not found") from exc
    except InactiveCampaignError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    response = repository.get_by_id(new_sighting.id)
    if response is None:
        raise HTTPException(status_code=500, detail="Unable to load created sighting")
    return response


@router.get("/sightings/{sighting_id}", response_model=SightingResponse)
def get_sighting(sighting_id: str, db: Session = Depends(get_db)):
    repository = SightingRepository(db)
    sighting = repository.get_by_id(sighting_id)
    if sighting is None:
        raise HTTPException(status_code=404, detail="Sighting not found")
    return sighting


@router.delete("/sightings/{sighting_id}", response_model=MessageResponse)
def delete_sighting(
    sighting_id: str,
    principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    repository = SightingRepository(db)
    sighting = repository.get_raw_by_id(sighting_id)
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    if sighting.ranger_id != principal.user_id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own sightings"
        )

    service = SightingCommandService(repository, CampaignRepository(db))
    try:
        service.delete_sighting(sighting)
    except CampaignLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MessageResponse(detail="Sighting deleted")
