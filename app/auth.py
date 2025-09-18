import time
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from redis import Redis

from .config import settings  # <- correct: same package, single dot

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, hashed: str) -> bool:
    return pwd_context.verify(p, hashed)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.jwt_expire_minutes
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        return payload.get("sub")
    except JWTError:
        return None


def issue_otp(mobile: str) -> str:
    # mock OTP for assignment/demo
    otp = str(int(time.time()))[-6:]
    redis_client.setex(f"otp:{mobile}", 300, otp)
    return otp


def verify_otp(mobile: str, otp: str) -> bool:
    key = f"otp:{mobile}"
    val = redis_client.get(key)
    if val and val == otp:
        redis_client.delete(key)
        return True
    return False
