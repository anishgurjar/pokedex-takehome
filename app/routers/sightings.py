from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import AppUser, Pokemon, Sighting
from app.schemas import MessageResponse, SightingCreate, SightingResponse

router = APIRouter(tags=["sightings"])


def _get_ranger_or_raise(db: Session, x_user_id: str | None) -> AppUser:
    """Resolve X-User-ID to an active ranger, raising appropriate HTTP errors."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header is required")
    user = db.query(AppUser).filter(AppUser.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.role != "ranger":
        raise HTTPException(status_code=403, detail="Only rangers can log sightings")
    return user


@router.post("/sightings", response_model=SightingResponse)
def create_sighting(
    sighting: SightingCreate,
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    ranger = _get_ranger_or_raise(db, x_user_id)

    pokemon = db.query(Pokemon).filter(Pokemon.id == sighting.pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    new_sighting = Sighting(
        pokemon_id=sighting.pokemon_id,
        ranger_id=x_user_id,
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
    resp.ranger_name = ranger.display_name
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
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(None),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header is required")

    sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    if sighting.ranger_id != x_user_id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own sightings"
        )

    db.delete(sighting)
    db.commit()
    return MessageResponse(detail="Sighting deleted")
