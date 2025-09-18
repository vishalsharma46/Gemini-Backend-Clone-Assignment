# app/services/gemini.py
import os
import httpx
from loguru import logger
from ..config import settings

GEN_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{settings.gemini_model}:generateContent"
)

# (Optional) quick dev toggle to prove pipeline without calling Gemini
USE_ECHO = os.getenv("USE_ECHO_AI", "").strip() == "1"

SYSTEM_PROMPT = (
    "You are **Gemini Backend Bot**. Be concise and helpful. "
    "If the user asks your name, answer exactly: 'Gemini Backend Bot'. "
    "Use prior messages in this chat for context."
)

def _build_contents(history, user_text: str):
    contents = []
    if history:
        for m in history[-10:]:
            if isinstance(m, dict):
                role_val = m.get("role", "")
                content_val = m.get("content", "")
            else:
                role_val = getattr(m, "role", "") or ""
                content_val = getattr(m, "content", "") or ""
            role = "user" if role_val.lower() == "user" else "model"
            contents.append({"role": role, "parts": [{"text": content_val}]})
    contents.append({"role": "user", "parts": [{"text": user_text or ""}]})
    return contents

def generate_gemini_response(user_text: str, history=None) -> str:
    if USE_ECHO:
        return f"ECHO: {user_text}"

    headers = {
        "x-goog-api-key": settings.gemini_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": _build_contents(history, user_text),
        # System instruction helps reduce generic greetings
        "systemInstruction": {"role": "system", "parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 256,
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(GEN_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        for cand in data.get("candidates", []):
            parts = (cand.get("content") or {}).get("parts") or []
            for p in parts:
                t = p.get("text")
                if isinstance(t, str) and t.strip():
                    return t

        logger.warning("Gemini returned no text candidates: {}", data)
        return "Sorry, I couldn’t generate a response."
    except Exception as e:
        logger.exception("Gemini API error: {}", e)
        return "Gemini API error, please try again later."
