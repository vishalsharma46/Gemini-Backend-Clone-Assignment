from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import get_current_user
from ..schemas import UserOut
from ..database import get_db
from ..utils import api_ok

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me")
def me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    return api_ok({"user": UserOut.model_validate(current).model_dump()})
