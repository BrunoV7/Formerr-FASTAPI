# app/core/middleware.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings


def setup_middleware(app: FastAPI):
    """Setup all middlewares"""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Session middleware for OAuth
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET
    )