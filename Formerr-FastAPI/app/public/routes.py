from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.forms.models import SubmissionCreate, Submission
from app.database.services import forms_service, submissions_service, user_service
from app.database.connection import get_db
from app.dependencies import get_optional_user
from datetime import datetime
import hashlib

router = APIRouter()


def hash_ip(ip: str) -> str:
    """Hash do IP para privacidade"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def get_client_ip(request: Request) -> str:
    """Extrai IP real do cliente"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


@router.get("/forms/{form_id}")
async def get_public_form(
        form_id: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Busca formulário público para preenchimento"""
    form = await forms_service.get_public_form(db, form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado ou não é público"
        )

    # Incrementar view count (analytics)
    # TODO: Implementar FormAnalytics se necessário

    # Preparar dados do formulário
    form_data = {
        "id": form.id,
        "title": form.title,
        "description": form.description,
        "questions": form.questions or [],
        "sections": form.sections or [],
        "settings": form.settings or {},
        "created_at": form.created_at.isoformat(),
        "submission_count": form.submission_count
    }

    # Adicionar informações extras para renderização
    form_data.update({
        "total_questions": len(form.questions or []),
        "estimated_time": len(form.questions or []) * 30,  # 30s por pergunta
        "requires_auth": form.settings.get("require_login", False) if form.settings else False,
        "user_authenticated": user is not None,
        "user_info": {
            "username": user.get("username") if user else None,
            "name": user.get("name") if user else None,
            "email": user.get("email") if user else None
        } if user else None
    })

    return {
        "success": True,
        "form": form_data,
        "meta": {
            "can_submit": True,
            "submission_count": form.submission_count,
            "owner": {
                "username": form.owner.username if form.owner else "unknown",
                "avatar_url": f"https://github.com/{form.owner.username}.png" if form.owner else None
            }
        }
    }


@router.post("/forms/{form_id}/submit")
async def submit_public_form(
        form_id: str,
        submission_data: SubmissionCreate,
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """Submete resposta para formulário público"""
    form = await forms_service.get_public_form(db, form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado ou não é público"
        )

    # Verificar se requer autenticação
    requires_login = form.settings.get("require_login", False) if form.settings else False
    if requires_login and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Este formulário requer autenticação"
        )

    # Validar respostas obrigatórias
    form_questions = form.questions or []
    required_questions = [q for q in form_questions if q.get("required", False)]
    submitted_question_ids = {answer.question_id for answer in submission_data.answers}

    missing_required = []
    for req_q in required_questions:
        if req_q.get("id") not in submitted_question_ids:
            missing_required.append(req_q.get("title", "Pergunta sem título"))

    if missing_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Perguntas obrigatórias não respondidas: {', '.join(missing_required)}"
        )

    # Preparar dados do submitter
    client_ip = get_client_ip(request)
    submitter_data = {
        "email": submission_data.submitter_email or (user.get("email") if user else None),
        "name": submission_data.submitter_name or (user.get("name") if user else None),
        "ip_hash": hash_ip(client_ip),
        "user_id": None
    }

    # Se usuário logado, buscar/criar no banco
    if user:
        db_user = await user_service.get_or_create_user(db, user)
        submitter_data["user_id"] = db_user.id

    # Criar submissão
    try:
        submission = await submissions_service.create_submission(
            db=db,
            form_id=form_id,
            answers=submission_data.answers,
            submitter_data=submitter_data
        )

        # Resposta de sucesso
        thank_you_message = "Obrigado por preencher o formulário!"
        redirect_url = None

        if form.settings:
            thank_you_message = form.settings.get("thank_you_message", thank_you_message)
            redirect_url = form.settings.get("redirect_url")

        return {
            "success": True,
            "submission": {
                "id": submission.id,
                "form_id": form_id,
                "submitted_at": submission.submitted_at.isoformat(),
                "total_answers": len(submission.answers)
            },
            "message": thank_you_message,
            "redirect_url": redirect_url,
            "form_title": form.title
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar submissão: {str(e)}"
        )


@router.get("/forms/{form_id}/preview")
async def preview_public_form(
        form_id: str,
        db: AsyncSession = Depends(get_db)
):
    """Preview do formulário público (sem possibilidade de submit)"""
    form = await forms_service.get_public_form(db, form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado ou não é público"
        )

    return {
        "success": True,
        "form": {
            "id": form.id,
            "title": form.title,
            "description": form.description,
            "questions": form.questions or [],
            "sections": form.sections or [],
            "settings": form.settings or {}
        },
        "preview": True,
        "meta": {
            "total_questions": len(form.questions or []),
            "owner": form.owner.username if form.owner else "unknown",
            "created_at": form.created_at.isoformat()
        }
    }


@router.get("/forms/{form_id}/embed")
async def get_embed_code(
        form_id: str,
        db: AsyncSession = Depends(get_db)
):
    """Código embed para formulário"""
    form = await forms_service.get_public_form(db, form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado ou não é público"
        )

    # URLs para diferentes ambientes
    base_url = "http://localhost:3000"  # TODO: usar config para produção
    embed_url = f"{base_url}/embed/{form_id}"

    embed_code = f'''<iframe 
    src="{embed_url}"
    width="100%" 
    height="600" 
    frameborder="0"
    style="border: 1px solid #e1e5e9; border-radius: 8px;"
    title="{form.title}">
</iframe>'''

    responsive_embed = f'''<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden; border-radius: 8px;">
    <iframe 
        src="{embed_url}"
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 1px solid #e1e5e9;"
        frameborder="0"
        title="{form.title}">
    </iframe>
</div>'''

    return {
        "success": True,
        "form_id": form_id,
        "form_title": form.title,
        "embed": {
            "url": embed_url,
            "html": embed_code,
            "responsive_html": responsive_embed,
            "javascript": f'''<script>
window.formerrEmbed = {{
    formId: '{form_id}',
    baseUrl: '{base_url}',
    load: function() {{
        const iframe = document.createElement('iframe');
        iframe.src = '{embed_url}';
        iframe.style.width = '100%';
        iframe.style.height = '600px';
        iframe.style.border = '1px solid #e1e5e9';
        iframe.style.borderRadius = '8px';
        iframe.title = '{form.title}';
        return iframe;
    }}
}};
</script>'''
        }
    }


# Endpoint para buscar múltiplos formulários públicos (para marketplace futuro)
@router.get("/forms")
async def get_public_forms(
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """Lista formulários públicos (para marketplace futuro)"""
    # TODO: Implementar busca avançada com filtros
    # Por enquanto, retorna lista vazia
    return {
        "success": True,
        "forms": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "message": "Marketplace de formulários públicos - em desenvolvimento"
    }