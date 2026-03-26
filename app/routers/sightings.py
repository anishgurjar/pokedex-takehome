from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import CurrentPrincipal, require_role
from app.deps import get_db
from app.models import AppUser, Pokemon, Sighting
from app.schemas import MessageResponse, SightingCreate, SightingResponse

router = APIRouter(tags=["sightings"])


@router.post("/sightings", response_model=SightingResponse)
def create_sighting(
    sighting: SightingCreate,
    principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    pokemon = db.query(Pokemon).filter(Pokemon.id == sighting.pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    new_sighting = Sighting(
        pokemon_id=sighting.pokemon_id,
        ranger_id=principal.user_id,
        region=sighting.region,
        route=sighting.route,
        date=sighting.date,
        weather=sighting.weather,
        time_of_day=sighting.time_of_day,
        height=sighting.height,
        weight=sighting.weight,
        is_shiny=sighting.is_shiny,
        notes=sighting.notes,
        latitude=sighting.latitude,
        longitude=sighting.longitude,
    )
    db.add(new_sighting)
    db.commit()
    db.refresh(new_sighting)

    resp = SightingResponse.model_validate(new_sighting)
    resp.pokemon_name = pokemon.name
    resp.ranger_name = principal.display_name
    return resp


@router.get("/sightings/{sighting_id}", response_model=SightingResponse)
def get_sighting(sighting_id: str, db: Session = Depends(get_db)):
    sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    pokemon = db.query(Pokemon).filter(Pokemon.id == sighting.pokemon_id).first()
    ranger = db.query(AppUser).filter(AppUser.id == sighting.ranger_id).first()

    resp = SightingResponse.model_validate(sighting)
    resp.pokemon_name = pokemon.name if pokemon else None
    resp.ranger_name = ranger.display_name if ranger else None
    return resp


@router.delete("/sightings/{sighting_id}", response_model=MessageResponse)
def delete_sighting(
    sighting_id: str,
    principal: Annotated[CurrentPrincipal, Depends(require_role("ranger"))],
    db: Session = Depends(get_db),
):
    sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    if sighting.ranger_id != principal.user_id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own sightings"
        )

    db.delete(sighting)
    db.commit()
    return MessageResponse(detail="Sighting deleted")
