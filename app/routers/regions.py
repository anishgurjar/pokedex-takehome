from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.repositories.regions import RegionRepository
from app.schemas import RegionSummaryResponse
from app.services.regions import RegionService

router = APIRouter(tags=["regions"])


@router.get("/regions/{region_name}/summary", response_model=RegionSummaryResponse)
def get_region_summary(region_name: str, db: Session = Depends(get_db)):
    try:
        return RegionService(RegionRepository(db)).get_summary(region_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
