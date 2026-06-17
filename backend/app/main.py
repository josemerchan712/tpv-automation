import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401
from app.routers import auth, categories, products, sales, reports, employees


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
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(reports.router)
app.include_router(employees.router)


@app.get("/health")
def health():
    return {"status": "ok"}
