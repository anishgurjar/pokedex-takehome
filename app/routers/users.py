from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import AppUser
from app.schemas import UserLookupResponse

router = APIRouter(tags=["users"])


@router.get("/users/lookup", response_model=UserLookupResponse)
def lookup_user(name: str = Query(...), db: Session = Depends(get_db)):
    user = (
        db.query(AppUser)
        .filter(AppUser.display_name_normalized == name.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserLookupResponse(id=user.id, name=user.display_name, role=user.role)
