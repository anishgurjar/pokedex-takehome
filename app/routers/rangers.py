from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_db
from app.domain.users import UserRole
from app.models import AppUser, Ranger
from app.repositories.sightings import SightingRepository
from app.schemas import RangerCreate, RangerResponse, SightingResponse
from app.services.users import (
    DuplicateUserError,
    assert_email_available,
    build_app_user,
    translate_user_integrity_error,
)

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


@router.post("/rangers", response_model=RangerResponse)
def create_ranger(ranger: RangerCreate, db: Session = Depends(get_db)):
    try:
        assert_email_available(db, ranger.email)
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=exc.detail) from exc

    user = build_app_user(role=UserRole.RANGER, name=ranger.name, email=ranger.email)
    db.add(user)
    ranger_profile = Ranger(user_id=user.id, specialization=ranger.specialization)
    db.add(ranger_profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicate_user_error = translate_user_integrity_error(exc)
        if duplicate_user_error is None:
            raise
        raise HTTPException(
            status_code=409,
            detail=duplicate_user_error.detail,
        ) from exc
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
    return SightingRepository(db).list_for_ranger(ranger_id)
