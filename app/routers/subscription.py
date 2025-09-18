from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
import stripe

from ..config import settings
from ..deps import get_current_user
from ..database import get_db, SessionLocal
from .. import models
from ..schemas import SubscriptionStatus
from ..utils import api_ok, api_error

router = APIRouter(prefix="", tags=["subscription"])

stripe.api_key = settings.stripe_secret_key


@router.post("/subscribe/pro")
def subscribe_pro(current=Depends(get_current_user)):
    if not settings.stripe_price_id_pro:
        api_error("Stripe price not configured", 400)

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        # Link checkout session to the current user so webhook can upgrade them
        client_reference_id=str(current.id),
        metadata={"user_id": str(current.id)},
    )
    return api_ok({"checkout_url": session.url})


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = (session.get("metadata") or {}).get("user_id") or session.get(
            "client_reference_id"
        )
        if user_id:
            db = SessionLocal()
            try:
                user = db.get(models.User, int(user_id))
                if user:
                    user.tier = models.Tier.PRO
                    db.commit()
            finally:
                db.close()

    return {"received": True}


@router.get("/subscription/status", response_model=SubscriptionStatus)
def subscription_status(current=Depends(get_current_user)):
    return SubscriptionStatus(
        tier=current.tier.value,
        status="active" if current.tier == models.Tier.PRO else "inactive",
    )
