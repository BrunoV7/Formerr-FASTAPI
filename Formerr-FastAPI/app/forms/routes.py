from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.forms.models import Form, FormCreate, FormUpdate, FormSummary
from app.database.services import forms_service, user_service
from app.database.connection import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[FormSummary])
async def get_user_forms(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Lista todos os formulários do usuário"""
    # Garantir que usuário existe no banco
    user = await user_service.get_or_create_user(db, current_user)

    # Buscar formulários
    forms = await forms_service.get_user_forms(db, user.id)

    # Converter para FormSummary
    forms_summary = []
    for form in forms:
        forms_summary.append(FormSummary(
            id=form.id,
            title=form.title,
            description=form.description,
            public=form.public,
            created_at=form.created_at,
            submission_count=form.submission_count,
            last_submission=form.last_submission
        ))

    return forms_summary


@router.post("/", response_model=Form, status_code=status.HTTP_201_CREATED)
async def create_form(
        form_data: FormCreate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Cria um novo formulário"""
    try:
        # Garantir que usuário existe no banco
        user = await user_service.get_or_create_user(db, current_user)

        # Criar formulário
        form = await forms_service.create_form(db, form_data, user.id)

        # Converter para schema de resposta
        return Form(
            id=form.id,
            title=form.title,
            description=form.description,
            public=form.public,
            owner_id=form.owner_id,
            owner_username=current_user["username"],
            created_at=form.created_at,
            updated_at=form.updated_at,
            questions=form.questions,
            sections=form.sections,
            settings=form.settings,
            submission_count=form.submission_count,
            last_submission=form.last_submission
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar formulário: {str(e)}"
        )


@router.get("/{form_id}", response_model=Form)
async def get_form(
        form_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Busca formulário específico do usuário"""
    user = await user_service.get_or_create_user(db, current_user)

    form = await forms_service.get_form_by_id(db, form_id, user.id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    return Form(
        id=form.id,
        title=form.title,
        description=form.description,
        public=form.public,
        owner_id=form.owner_id,
        owner_username=current_user["username"],
        created_at=form.created_at,
        updated_at=form.updated_at,
        questions=form.questions,
        sections=form.sections,
        settings=form.settings,
        submission_count=form.submission_count,
        last_submission=form.last_submission
    )


@router.put("/{form_id}", response_model=Form)
async def update_form(
        form_id: str,
        update_data: FormUpdate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Atualiza formulário"""
    user = await user_service.get_or_create_user(db, current_user)

    form = await forms_service.update_form(db, form_id, update_data, user.id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    return Form(
        id=form.id,
        title=form.title,
        description=form.description,
        public=form.public,
        owner_id=form.owner_id,
        owner_username=current_user["username"],
        created_at=form.created_at,
        updated_at=form.updated_at,
        questions=form.questions,
        sections=form.sections,
        settings=form.settings,
        submission_count=form.submission_count,
        last_submission=form.last_submission
    )


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
        form_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Deleta formulário"""
    user = await user_service.get_or_create_user(db, current_user)

    deleted = await forms_service.delete_form(db, form_id, user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )


@router.get("/{form_id}/stats")
async def get_form_stats(
        form_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Estatísticas do formulário"""
    user = await user_service.get_or_create_user(db, current_user)

    form = await forms_service.get_form_by_id(db, form_id, user.id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    return {
        "form_id": form_id,
        "title": form.title,
        "total_submissions": form.submission_count,
        "last_submission": form.last_submission,
        "created_at": form.created_at,
        "total_questions": len(form.questions or []),
        "is_public": form.public,
        "view_url": f"/forms/{form_id}",
        "public_url": f"/public/forms/{form_id}" if form.public else None,
        "owner": current_user["username"]
    }