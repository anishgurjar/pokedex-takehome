from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import AppUser, Pokemon, Ranger, Sighting
from app.schemas import RangerCreate, RangerResponse, SightingResponse

router = APIRouter(tags=["rangers"])


def _ranger_response(user: AppUser, ranger: Ranger) -> RangerResponse:
    return RangerResponse(
        id=user.id,
        name=user.display_name,
        email=user.email,
        specialization=ranger.specialization,
        status=user.status,
        created_at=user.created_at,
    )


def _assert_email_available(db: Session, email: str) -> None:
    existing = (
        db.query(AppUser)
        .filter(AppUser.email_normalized == email.strip().lower())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"User already exists with role '{existing.role}'",
        )


@router.post("/rangers", response_model=RangerResponse)
def create_ranger(ranger: RangerCreate, db: Session = Depends(get_db)):
    _assert_email_available(db, ranger.email)
    user = AppUser(
        role="ranger",
        display_name=ranger.name,
        display_name_normalized=ranger.name.strip().lower(),
        email=ranger.email,
        email_normalized=ranger.email.strip().lower(),
    )
    db.add(user)
    ranger_profile = Ranger(user_id=user.id, specialization=ranger.specialization)
    db.add(ranger_profile)
    db.commit()
    db.refresh(user)
    db.refresh(ranger_profile)
    return _ranger_response(user, ranger_profile)


@router.get("/rangers/{ranger_id}", response_model=RangerResponse)
def get_ranger(ranger_id: str, db: Session = Depends(get_db)):
    user = (
        db.query(AppUser)
        .filter(AppUser.id == ranger_id, AppUser.role == "ranger")
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Ranger not found")
    ranger_profile = db.query(Ranger).filter(Ranger.user_id == ranger_id).first()
    return _ranger_response(user, ranger_profile)


@router.get("/rangers/{ranger_id}/sightings", response_model=list[SightingResponse])
def get_ranger_sightings(ranger_id: str, db: Session = Depends(get_db)):
    user = (
        db.query(AppUser)
        .filter(AppUser.id == ranger_id, AppUser.role == "ranger")
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Ranger not found")
    sightings = db.query(Sighting).filter(Sighting.ranger_id == ranger_id).all()
    result = []
    for s in sightings:
        pokemon = db.query(Pokemon).filter(Pokemon.id == s.pokemon_id).first()
        resp = SightingResponse.model_validate(s)
        resp.pokemon_name = pokemon.name if pokemon else None
        resp.ranger_name = user.display_name
        result.append(resp)
    return result
