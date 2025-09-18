from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.services.gemini import generate_gemini_response


def handle_gemini_message(chatroom_id: int, user_message_id: int):
    db: Session = SessionLocal()
    try:
        msgs = (
            db.query(models.Message)
            .filter(models.Message.chatroom_id == chatroom_id)
            .order_by(models.Message.created_at.asc())
            .all()
        )


        user_msg = next((m for m in msgs if m.id == user_message_id), None)
        if not user_msg:

            user_msg = next(
                (m for m in reversed(msgs) if (m.role or "").lower() == "user"),
                None,
            )
        user_text = (user_msg.content if user_msg else "") or ""

        if user_msg:
            cutoff = [m for m in msgs if m.created_at < user_msg.created_at]
        else:
            cutoff = msgs[:-1]
        history = [{"role": m.role, "content": m.content} for m in cutoff][-20:]

        text = generate_gemini_response(user_text=user_text, history=history)

        assistant = models.Message(
            chatroom_id=chatroom_id,
            role="assistant",
            content=text,
            processed=True,
        )
        db.add(assistant)
        db.commit()
    finally:
        db.close()
