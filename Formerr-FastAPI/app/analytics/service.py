from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, extract
from sqlalchemy.future import select
from app.database.models import Form, Submission, User, FormAnalytics


class AnalyticsService:
    """Beast mode analytics for dashboard"""

    @staticmethod
    async def get_dashboard_overview(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Dashboard overview stats"""

        # Total forms
        forms_result = await db.execute(
            select(func.count(Form.id)).where(Form.owner_id == user_id)
        )
        total_forms = forms_result.scalar() or 0

        # Total submissions (all forms)
        submissions_result = await db.execute(
            select(func.count(Submission.id))
            .join(Form)
            .where(Form.owner_id == user_id)
        )
        total_submissions = submissions_result.scalar() or 0

        # Submissions this month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_submissions_result = await db.execute(
            select(func.count(Submission.id))
            .join(Form)
            .where(
                and_(
                    Form.owner_id == user_id,
                    Submission.submitted_at >= current_month_start
                )
            )
        )
        month_submissions = month_submissions_result.scalar() or 0

        # Top performing form
        top_form_result = await db.execute(
            select(Form.title, Form.submission_count)
            .where(Form.owner_id == user_id)
            .order_by(Form.submission_count.desc())
            .limit(1)
        )
        top_form = top_form_result.first()

        # Growth rate (compare with last month)
        last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
        last_month_end = current_month_start - timedelta(seconds=1)

        last_month_result = await db.execute(
            select(func.count(Submission.id))
            .join(Form)
            .where(
                and_(
                    Form.owner_id == user_id,
                    Submission.submitted_at >= last_month_start,
                    Submission.submitted_at <= last_month_end
                )
            )
        )
        last_month_submissions = last_month_result.scalar() or 0

        growth_rate = 0
        if last_month_submissions > 0:
            growth_rate = ((month_submissions - last_month_submissions) / last_month_submissions) * 100

        return {
            "overview": {
                "total_forms": total_forms,
                "total_submissions": total_submissions,
                "month_submissions": month_submissions,
                "growth_rate": round(growth_rate, 2),
                "top_form": {
                    "title": top_form[0] if top_form else "Nenhum",
                    "submissions": top_form[1] if top_form else 0
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "period": "current_month"
        }

    @staticmethod
    async def get_submissions_timeline(
            db: AsyncSession,
            user_id: int,
            days: int = 30
    ) -> Dict[str, Any]:
        """Submissions timeline for charts"""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Daily submissions
        daily_result = await db.execute(
            select(
                extract('day', Submission.submitted_at).label('day'),
                extract('month', Submission.submitted_at).label('month'),
                func.count(Submission.id).label('count')
            )
            .join(Form)
            .where(
                and_(
                    Form.owner_id == user_id,
                    Submission.submitted_at >= start_date
                )
            )
            .group_by(
                extract('day', Submission.submitted_at),
                extract('month', Submission.submitted_at)
            )
            .order_by(
                extract('month', Submission.submitted_at),
                extract('day', Submission.submitted_at)
            )
        )

        daily_data = []
        for row in daily_result:
            daily_data.append({
                "date": f"2025-{int(row.month):02d}-{int(row.day):02d}",
                "submissions": row.count
            })

        return {
            "timeline": daily_data,
            "period_days": days,
            "total_points": len(daily_data)
        }

    @staticmethod
    async def get_top_forms_performance(
            db: AsyncSession,
            user_id: int,
            limit: int = 10
    ) -> Dict[str, Any]:
        """Top performing forms"""

        result = await db.execute(
            select(
                Form.id,
                Form.title,
                Form.submission_count,
                Form.created_at,
                func.count(Submission.id).label('recent_submissions')
            )
            .outerjoin(Submission)
            .where(Form.owner_id == user_id)
            .group_by(Form.id, Form.title, Form.submission_count, Form.created_at)
            .order_by(Form.submission_count.desc())
            .limit(limit)
        )

        top_forms = []
        for row in result:
            conversion_rate = 0
            # TODO: Calculate view count vs submissions for conversion rate

            top_forms.append({
                "form_id": row.id,
                "title": row.title,
                "total_submissions": row.submission_count,
                "recent_submissions": row.recent_submissions,
                "created_at": row.created_at.isoformat(),
                "conversion_rate": conversion_rate,
                "performance_score": row.submission_count * 10  # Simple scoring
            })

        return {
            "top_forms": top_forms,
            "total_analyzed": len(top_forms)
        }


# Instance
analytics_service = AnalyticsService()