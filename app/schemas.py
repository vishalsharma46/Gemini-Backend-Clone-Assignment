from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Tier(str, Enum):
    BASIC = "basic"
    PRO = "pro"

class SignupRequest(BaseModel):
    mobile: str
    password: Optional[str] = None

class SendOtpRequest(BaseModel):
    mobile: str

class VerifyOtpRequest(BaseModel):
    mobile: str
    otp: str

class ChangePasswordRequest(BaseModel):
    new_password: str

class UserOut(BaseModel):
    id: int
    mobile: str
    tier: Tier
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatroomCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

class ChatroomOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    class Config:
        from_attributes = True

class ChatroomDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageOut]
    class Config:
        from_attributes = True

class SubscriptionStatus(BaseModel):
    tier: Tier
    status: str
