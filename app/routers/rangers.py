from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Pokemon, Ranger, Sighting
from app.schemas import RangerCreate, RangerResponse, SightingResponse

router = APIRouter(tags=["rangers"])


@router.post("/rangers", response_model=RangerResponse)
def create_ranger(ranger: RangerCreate, db: Session = Depends(get_db)):
    new_ranger = Ranger(
        name=ranger.name,
        email=ranger.email,
        specialization=ranger.specialization,
    )
    db.add(new_ranger)
    db.commit()
    db.refresh(new_ranger)
    return new_ranger


@router.get("/rangers/{ranger_id}", response_model=RangerResponse)
def get_ranger(ranger_id: str, db: Session = Depends(get_db)):
    ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")
    return ranger


@router.get("/rangers/{ranger_id}/sightings", response_model=list[SightingResponse])
def get_ranger_sightings(ranger_id: str, db: Session = Depends(get_db)):
    ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")
    sightings = db.query(Sighting).filter(Sighting.ranger_id == ranger_id).all()
    result = []
    for s in sightings:
        pokemon = db.query(Pokemon).filter(Pokemon.id == s.pokemon_id).first()
        resp = SightingResponse.model_validate(s)
        resp.pokemon_name = pokemon.name if pokemon else None
        resp.ranger_name = ranger.name
        result.append(resp)
    return result
