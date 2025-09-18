from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .routers import auth, user, chatroom, subscription

app = FastAPI(title=settings.app_name)

app.mount("/demo", StaticFiles(directory="demo", html=True), name="demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chatroom.router)
app.include_router(subscription.router)

@app.get("/")
def root():
    return {"ok": True, "message": "Gemini Backend Clone API"}
