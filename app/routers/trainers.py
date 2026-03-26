from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import AppUser, Trainer
from app.schemas import TrainerCreate, TrainerResponse

router = APIRouter(tags=["trainers"])


def _trainer_response(user: AppUser) -> TrainerResponse:
    return TrainerResponse(
        id=user.id,
        name=user.display_name,
        email=user.email,
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


@router.post("/trainers", response_model=TrainerResponse)
def create_trainer(trainer: TrainerCreate, db: Session = Depends(get_db)):
    _assert_email_available(db, trainer.email)
    user = AppUser(
        role="trainer",
        display_name=trainer.name,
        display_name_normalized=trainer.name.strip().lower(),
        email=trainer.email,
        email_normalized=trainer.email.strip().lower(),
    )
    db.add(user)
    db.add(Trainer(user_id=user.id))
    db.commit()
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
