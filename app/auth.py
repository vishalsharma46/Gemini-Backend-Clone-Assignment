from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import SendOtpRequest, VerifyOtpRequest, ChangePasswordRequest, TokenResponse
from ..auth import issue_otp, verify_otp, create_access_token, hash_password
from ..utils import api_ok, api_error
from ..deps import get_current_user
from pydantic import BaseModel

class SignupIn(BaseModel):
    mobile: str 

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(body: SignupIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(mobile=body.mobile).first()
    if not user:
        user = models.User(mobile=body.mobile, tier=models.Tier.BASIC)
        db.add(user)
    db.commit()
    return api_ok({"user_id": user.id}, "signed_up")

@router.post("/send-otp")
def send_otp(body: SendOtpRequest):
    otp = issue_otp(body.mobile)
    return api_ok({"mobile": body.mobile, "otp": otp}, "OTP issued (mocked)")

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp_endpoint(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    ok = verify_otp(body.mobile, body.otp)
    if not ok:
        api_error("Invalid OTP", 400)

    user = db.query(models.User).filter(models.User.mobile == body.mobile).first()
    if not user:
        user = models.User(mobile=body.mobile)  
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.mobile)
    return TokenResponse(access_token=token)

@router.post("/forgot-password")
def forgot_password(body: SendOtpRequest):
    otp = issue_otp(body.mobile)
    return api_ok({"mobile": body.mobile, "otp": otp}, "Password reset OTP issued (mocked)")

@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current=Depends(get_current_user), db: Session = Depends(get_db)):
    current.password_hash = hash_password(body.new_password)
    db.add(current)
    db.commit()
    return api_ok(message="Password changed")
