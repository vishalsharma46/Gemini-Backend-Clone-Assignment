from pydantic import BaseModel
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Gemini Backend Clone")
    app_env: str = os.getenv("APP_ENV", "dev")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    app_debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"

    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/gemini_clone")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    stripe_public_key: str = os.getenv("STRIPE_PUBLIC_KEY", "")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_id_pro: str = os.getenv("STRIPE_PRICE_ID_PRO", "")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

settings = Settings()
