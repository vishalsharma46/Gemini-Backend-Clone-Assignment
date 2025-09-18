from datetime import datetime
from fastapi import APIRouter, Depends
from redis.exceptions import RedisError
from sqlalchemy.orm import Session
from loguru import logger
from ..config import settings

from ..deps import get_current_user
from .. import models
from ..models import Tier
from ..database import get_db
from ..schemas import (
    ChatroomCreate,
    ChatroomOut,
    ChatroomDetail,
    MessageCreate,
)
from ..utils import api_ok, api_error
from ..services.queue import gemini_queue
from ..cache import get_cached_chatrooms, set_cached_chatrooms, delete_cached_chatrooms
from ..ratelimit import increment_and_check  

router = APIRouter(prefix="/chatroom", tags=["chatroom"])

@router.post("")
def create_chatroom(
    body: ChatroomCreate,
    current=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = models.Chatroom(user_id=current.id, title=body.title)
    db.add(cr)
    db.commit()
    db.refresh(cr)

    # Bust per-user cache
    delete_cached_chatrooms(current.id)

    return api_ok(
        {"chatroom": ChatroomOut.model_validate(cr).model_dump(mode="json")},
        "Chatroom created",
    )

@router.get("")
def list_chatrooms(
    current=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cached = get_cached_chatrooms(current.id)  
    if cached is not None:
        return {"ok": True, "message": "ok (cache)", "data": {"chatrooms": cached}}

    rows = (
        db.query(models.Chatroom)
        .filter(models.Chatroom.user_id == current.id)
        .order_by(models.Chatroom.created_at.desc())
        .all()
    )
    payload = [ChatroomOut.model_validate(r).model_dump(mode="json") for r in rows]
    set_cached_chatrooms(current.id, payload, ttl_seconds=600)  # no-throw
    return {"ok": True, "message": "ok", "data": {"chatrooms": payload}}

@router.get("/{chatroom_id}")
def get_chatroom(
    chatroom_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = (
        db.query(models.Chatroom)
        .filter(
            models.Chatroom.id == chatroom_id,
            models.Chatroom.user_id == current.id,
        )
        .first()
    )
    if not cr:
        return api_error("Chatroom not found", 404)

    detail = ChatroomDetail.model_validate(
        {
            "id": cr.id,
            "title": cr.title,
            "created_at": cr.created_at,
            "messages": cr.messages,
        }
    )
    return api_ok({"chatroom": detail.model_dump(mode="json")})

@router.post("/{chatroom_id}/message")
def send_message(
    chatroom_id: int,
    body: MessageCreate,
    current=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = (
        db.query(models.Chatroom)
        .filter(
            models.Chatroom.id == chatroom_id,
            models.Chatroom.user_id == current.id,
        )
        .first()
    )
    if not cr:
        return api_error("Chatroom not found", 404)

    if current.tier == Tier.BASIC:
        try:
            dev_limit = 50 if settings.app_env == "dev" else 5
            allowed = increment_and_check(current.id, limit=dev_limit)
        except Exception as e: 
            logger.warning(f"Rate-limit unavailable; allowing request. err={e}")
            allowed = True

        if not allowed:
            return api_error(
                "Daily prompt limit reached for Basic plan. Upgrade to Pro.",
                429,
            )

    user_msg = models.Message(
        chatroom_id=cr.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)


    try:
        job = gemini_queue.enqueue(
            "worker_tasks.handle_gemini_message",
            cr.id,
            user_msg.id,
        )
        return api_ok(
            {"message_id": user_msg.id, "job_id": job.get_id()},
            "Message queued",
        )
    except RedisError as e:
        logger.exception("Queue enqueue failed")
        return api_error("Queue unavailable, please try again later.", 503)
