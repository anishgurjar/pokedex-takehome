from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Trainer
from app.schemas import TrainerCreate, TrainerResponse

router = APIRouter(tags=["trainers"])


@router.post("/trainers")
def create_trainer(trainer: TrainerCreate, db: Session = Depends(get_db)) -> Trainer:
    new_trainer = Trainer(name=trainer.name, email=trainer.email)
    db.add(new_trainer)
    db.commit()
    db.refresh(new_trainer)
    return new_trainer


@router.get("/trainers/{trainer_id}", response_model=TrainerResponse)
def get_trainer(trainer_id: str, db: Session = Depends(get_db)):
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return trainer
