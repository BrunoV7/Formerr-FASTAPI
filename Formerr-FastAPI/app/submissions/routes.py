from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.services import submissions_service, user_service
from app.database.connection import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/forms/{form_id}/submissions")
async def get_form_submissions(
        form_id: str,
        limit: int = Query(50, le=200),
        offset: int = Query(0, ge=0),
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Lista submissões de um formulário (apenas owner)"""
    user = await user_service.get_or_create_user(db, current_user)

    submissions = await submissions_service.get_form_submissions(
        db=db,
        form_id=form_id,
        owner_id=user.id,
        limit=limit
    )

    # Converter para formato de resposta
    submissions_data = []
    for submission in submissions:
        submissions_data.append({
            "id": submission.id,
            "submitted_at": submission.submitted_at.isoformat(),
            "answers": submission.answers,
            "submitter": {
                "email": submission.submitter_email,
                "name": submission.submitter_name,
                "is_registered": submission.submitter_user_id is not None
            },
            "answer_count": len(submission.answers) if submission.answers else 0
        })

    return {
        "success": True,
        "form_id": form_id,
        "submissions": submissions_data,
        "total": len(submissions_data),
        "limit": limit,
        "offset": offset
    }


@router.get("/forms/{form_id}/submissions/stats")
async def get_submission_stats(
        form_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Estatísticas detalhadas de submissões"""
    user = await user_service.get_or_create_user(db, current_user)

    stats = await submissions_service.get_submission_stats(
        db=db,
        form_id=form_id,
        owner_id=user.id
    )

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    return {
        "success": True,
        **stats,
        "owner": current_user["username"]
    }


@router.get("/forms/{form_id}/submissions/export")
async def export_submissions(
        form_id: str,
        format: str = Query("json", regex="^(json|csv)$"),
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Exporta submissões em JSON ou CSV"""
    user = await user_service.get_or_create_user(db, current_user)

    submissions = await submissions_service.get_form_submissions(
        db=db,
        form_id=form_id,
        owner_id=user.id,
        limit=1000  # Limite para export
    )

    if format == "json":
        export_data = []
        for submission in submissions:
            export_data.append({
                "submission_id": submission.id,
                "submitted_at": submission.submitted_at.isoformat(),
                "submitter_email": submission.submitter_email,
                "submitter_name": submission.submitter_name,
                "answers": submission.answers
            })

        return {
            "success": True,
            "format": "json",
            "form_id": form_id,
            "export_date": "2025-06-18T03:09:25Z",
            "total_submissions": len(export_data),
            "data": export_data
        }

    elif format == "csv":
        # TODO: Implementar export CSV
        return {
            "success": True,
            "format": "csv",
            "message": "CSV export em desenvolvimento",
            "form_id": form_id
        }