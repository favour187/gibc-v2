"""Application entry point for Adaptive Learning Studio (GIBC V2).

Run locally:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.core.config import Settings
from app.core.http import create_app
from app.features.learning.routers import router as feature_router
from app.settings import AppSettings


def build_app(settings: Settings | None = None) -> FastAPI:
    """Build the app; pass test settings in tests, otherwise use the env."""
    settings = settings or AppSettings.from_env()
    from app.features.learning.ai_skills import LOCAL_SKILLS

    return create_app(settings, extra_routers=[feature_router], local_skills=LOCAL_SKILLS)


app = build_app()
