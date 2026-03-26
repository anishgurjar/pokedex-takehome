from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_db
from app.domain.users import UserRole
from app.models import AppUser, Trainer
from app.schemas import TrainerCreate, TrainerResponse
from app.services.users import (
    DuplicateUserError,
    assert_email_available,
    build_app_user,
    translate_user_integrity_error,
)

router = APIRouter(tags=["trainers"])


def _trainer_response(user: AppUser) -> TrainerResponse:
    return TrainerResponse(
        id=user.id,
        name=user.display_name,
        email=user.email,
        status=user.status,
        created_at=user.created_at,
    )


@router.post("/trainers", response_model=TrainerResponse)
def create_trainer(trainer: TrainerCreate, db: Session = Depends(get_db)):
    try:
        assert_email_available(db, trainer.email)
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=exc.detail) from exc

    user = build_app_user(role=UserRole.TRAINER, name=trainer.name, email=trainer.email)
    db.add(user)
    db.add(Trainer(user_id=user.id))
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
    return _trainer_response(user)


@router.get("/trainers/{trainer_id}", response_model=TrainerResponse)
def get_trainer(trainer_id: str, db: Session = Depends(get_db)):
    user = (
        db.query(AppUser)
        .filter(AppUser.id == trainer_id, AppUser.role == "trainer")
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return _trainer_response(user)
