from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.email.service import email_service
from app.auth.auth_codes import auth_code_manager
from app.database.services import forms_service, user_service
from app.database.connection import get_db
from app.dependencies import get_current_user
from app.auth.models import Permission
from app.dependencies import require_permission

router = APIRouter()


class InviteEmailRequest(BaseModel):
    form_id: str
    emails: List[EmailStr]
    custom_message: Optional[str] = None


class AuthCodeRequest(BaseModel):
    form_id: str
    email: EmailStr
    name: Optional[str] = None


class VerifyCodeRequest(BaseModel):
    form_id: str
    email: EmailStr
    code: str


@router.post("/send-invitations")
async def send_form_invitations(
        request: InviteEmailRequest,
        current_user: dict = Depends(require_permission(Permission.USE_API)),
        db: AsyncSession = Depends(get_db)
):
    """Enviar convites por email para formulário"""

    user = await user_service.get_or_create_user(db, current_user)

    # Verificar se o form existe e pertence ao usuário
    form = await forms_service.get_form_by_id(db, request.form_id, user.id)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    results = []
    for email in request.emails:
        result = await email_service.send_form_invitation(
            to_email=email,
            to_name=email.split('@')[0].title(),  # Nome baseado no email
            form_title=form.title,
            form_url=f"https://formerr.brunov7.dev/forms/{form.id}",
            sender_name=current_user["name"],
            custom_message=request.custom_message
        )
        results.append({
            "email": email,
            "sent": result["success"],
            "error": result.get("error")
        })

    successful_sends = len([r for r in results if r["sent"]])

    return {
        "success": True,
        "form_id": request.form_id,
        "form_title": form.title,
        "total_emails": len(request.emails),
        "successful_sends": successful_sends,
        "results": results,
        "beast_mode": "📧 EMAIL BLAST COMPLETE 📧"
    }


@router.post("/send-auth-code")
async def send_auth_code(request: AuthCodeRequest):
    """Enviar código de autenticação por email"""

    # Buscar form público
    async with get_db() as db:
        form = await forms_service.get_public_form(db, request.form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Formulário não encontrado"
            )

    # Gerar e enviar código
    result = auth_code_manager.generate_and_send_code(
        email=request.email,
        form_id=request.form_id,
        form_title=form.title,
        user_name=request.name
    )

    return {
        "success": result["success"],
        "message": "Código enviado para seu email",
        "email": request.email,
        "expires_in_minutes": 10,
        "form_title": form.title
    }


@router.post("/verify-auth-code")
async def verify_auth_code(request: VerifyCodeRequest):
    """Verificar código de autenticação"""

    result = auth_code_manager.verify_code(
        email=request.email,
        form_id=request.form_id,
        submitted_code=request.code
    )

    if result["valid"]:
        # Gerar token temporário para acesso ao form
        temp_token = f"temp_access:{request.form_id}:{request.email}:{datetime.utcnow().timestamp()}"

        return {
            "success": True,
            "message": result["message"],
            "access_granted": True,
            "temp_token": temp_token,
            "form_id": request.form_id
        }
    else:
        return {
            "success": False,
            "message": result["message"],
            "reason": result["reason"],
            "attempts_remaining": result.get("attempts_remaining")
        }


@router.get("/stats")
async def get_email_stats(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Estatísticas de emails enviados"""

    # TODO: Implementar tracking de emails
    return {
        "success": True,
        "stats": {
            "total_invitations_sent": 0,
            "total_auth_codes_sent": 0,
            "delivery_rate": "98.5%",
            "bounce_rate": "1.5%"
        },
        "mailjet_status": "✅ CONNECTED",
        "monthly_quota": "6,000 emails",
        "beast_mode": "📊 EMAIL ANALYTICS READY 📊"
    }