from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.service import analytics_service
from app.database.services import user_service
from app.database.connection import get_db
from app.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.get("/dashboard/overview")
async def get_dashboard_overview(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Dashboard overview - Beast mode stats"""
    user = await user_service.get_or_create_user(db, current_user)

    overview = await analytics_service.get_dashboard_overview(db, user.id)

    return {
        "success": True,
        "user": current_user["username"],
        "analytics": overview,
        "beast_mode": "🔥 ACTIVATED 🔥"
    }


@router.get("/dashboard/timeline")
async def get_submissions_timeline(
        days: int = 30,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Submissions timeline for charts"""
    user = await user_service.get_or_create_user(db, current_user)

    timeline = await analytics_service.get_submissions_timeline(db, user.id, days)

    return {
        "success": True,
        "timeline": timeline,
        "chart_ready": True
    }


@router.get("/dashboard/top-forms")
async def get_top_forms_performance(
        limit: int = 10,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Top performing forms"""
    user = await user_service.get_or_create_user(db, current_user)

    performance = await analytics_service.get_top_forms_performance(db, user.id, limit)

    return {
        "success": True,
        "performance": performance,
        "insights_ready": True
    }


@router.get("/dashboard/real-time")
async def get_real_time_stats(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Real-time dashboard stats"""
    user = await user_service.get_or_create_user(db, current_user)

    # Last 24 hours activity
    timeline_24h = await analytics_service.get_submissions_timeline(db, user.id, 1)
    overview = await analytics_service.get_dashboard_overview(db, user.id)

    return {
        "success": True,
        "real_time": {
            "last_24h": timeline_24h,
            "current_stats": overview["overview"],
            "live": True,
            "refresh_interval": 30  # seconds
        },
        "timestamp": "2025-06-18T03:30:45Z",
        "beast_mode": "🚀 REAL-TIME ACTIVATED 🚀"
    }