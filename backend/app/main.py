import logging
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401 — registers all models with Base.metadata
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == "change-me-in-production":
        warnings.warn(
            "SECRET_KEY is using the insecure default value. "
            "Set the SECRET_KEY environment variable before deploying to production.",
            stacklevel=2,
        )
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TPV Automation", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
