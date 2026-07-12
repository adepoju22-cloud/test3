"""
FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Or via Docker Compose:
    docker compose up --build
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database.db import init_db
from app.utils.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database schema on startup."""
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=(
        "A fully local Security Compliance Dashboard that scans a JSON "
        "resource inventory against YAML-defined rules mapped to CIS, "
        "NIST, and ISO 27001, storing results in SQLite and exposing them "
        "via REST API and Grafana dashboards."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Health"])
def root() -> dict:
    """Basic health-check / welcome endpoint."""
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_env == "local"),
    )
