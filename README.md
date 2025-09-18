# Gemini Backend Clone (FastAPI)

A Gemini-style backend enabling OTP-based auth, user chatrooms, async Gemini API conversations via Redis Queue (RQ), and Stripe subscriptions. Includes a Streamlit frontend.

## Features
- **Auth:** Mobile + OTP (mock) and JWT sessions.
- **Chatrooms:** Create/list/detail; messages enqueued for Gemini response.
- **Async Queue:** RQ + Redis worker for Gemini calls.
- **Gemini Integration:** Google Generative Language API.
- **Stripe:** Checkout for Pro and webhook to activate subscription.
- **Rate limiting:** Basic plan = 5 prompts/day via Redis counters (dev: 50).
- **Caching:** `GET /chatroom` cached per-user in Redis (10 min).

## Tech
FastAPI, SQLAlchemy (PostgreSQL), Redis, RQ, Stripe, httpx, Streamlit, Docker Compose.

---

## Quickstart (Local)

### 1) Clone & env
```bash
cp .env.example .env          # fill values (do NOT commit secrets)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
