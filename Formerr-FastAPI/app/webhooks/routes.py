from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.webhooks.service import webhook_service
from app.webhooks.models import WebhookCreate, WebhookUpdate, WebhookResponse
from app.database.services import user_service
from app.database.connection import get_db
from app.dependencies import require_webhook_permission

router = APIRouter()


@router.post("/forms/{form_id}/webhooks", response_model=WebhookResponse)
async def create_webhook(
        form_id: str,
        webhook_data: WebhookCreate,
        current_user: Dict[str, Any] = Depends(require_webhook_permission()),
        db: AsyncSession = Depends(get_db)
):
    """Criar webhook para formulário"""

    user = await user_service.get_or_create_user(db, current_user)

    webhook = await webhook_service.create_webhook(
        db=db,
        form_id=form_id,
        webhook_data=webhook_data,
        owner_id=user.id
    )

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formulário não encontrado"
        )

    return WebhookResponse(
        id=webhook.id,
        form_id=webhook.form_id,
        url=webhook.url,
        events=webhook.events,
        active=webhook.active,
        created_at=webhook.created_at.isoformat(),
        last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
        failure_count=webhook.failure_count
    )


@router.get("/forms/{form_id}/webhooks", response_model=List[WebhookResponse])
async def list_form_webhooks(
        form_id: str,
        current_user: Dict[str, Any] = Depends(require_webhook_permission()),
        db: AsyncSession = Depends(get_db)
):
    """Listar webhooks de um formulário"""

    user = await user_service.get_or_create_user(db, current_user)

    webhooks = await webhook_service.get_form_webhooks(
        db=db,
        form_id=form_id,
        owner_id=user.id
    )

    return [
        WebhookResponse(
            id=webhook.id,
            form_id=webhook.form_id,
            url=webhook.url,
            events=webhook.events,
            active=webhook.active,
            created_at=webhook.created_at.isoformat(),
            last_triggered=webhook.last_triggered.isoformat() if webhook.last_triggered else None,
            failure_count=webhook.failure_count
        )
        for webhook in webhooks
    ]


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
        webhook_id: str,
        current_user: Dict[str, Any] = Depends(require_webhook_permission()),
        db: AsyncSession = Depends(get_db)
):
    """Testar webhook"""

    user = await user_service.get_or_create_user(db, current_user)

    result = await webhook_service.test_webhook(
        db=db,
        webhook_id=webhook_id,
        owner_id=user.id
    )

    if not result["success"]:
        return {
            "success": False,
            "message": "Falha ao testar webhook",
            "error": result.get("error"),
            "webhook_id": webhook_id
        }

    return {
        "success": True,
        "message": "🚀 Webhook testado com sucesso!",
        "webhook_id": webhook_id,
        "response_time_ms": result.get("response_time_ms"),
        "status_code": result.get("status_code"),
        "delivery_id": result.get("delivery_id"),
        "beast_mode": "🔗 WEBHOOK TEST COMPLETE 🔗"
    }


@router.get("/webhooks/events")
async def list_webhook_events():
    """Lista eventos disponíveis para webhooks"""

    from app.webhooks.models import WebhookEvent

    events = []
    for event in WebhookEvent:
        events.append({
            "name": event.value,
            "description": {
                "submission.created": "Disparado quando uma nova resposta é submetida",
                "submission.updated": "Disparado quando uma resposta é atualizada",
                "form.created": "Disparado quando um formulário é criado",
                "form.updated": "Disparado quando um formulário é atualizado",
                "form.deleted": "Disparado quando um formulário é deletado",
                "user.registered": "Disparado quando um usuário se registra"
            }.get(event.value, "Evento webhook")
        })

    return {
        "success": True,
        "events": events,
        "total_events": len(events),
        "webhook_guide": {
            "signature_header": "X-Formerr-Signature",
            "event_header": "X-Formerr-Event",
            "delivery_header": "X-Formerr-Delivery",
            "timestamp_header": "X-Formerr-Timestamp",
            "user_agent": "Formerr-Webhooks/1.0 (BrunoV7)"
        },
        "example_payload": {
            "event": "submission.created",
            "timestamp": "2025-06-18T03:44:14Z",
            "form_id": "form_20250618_034414_abc123",
            "data": {
                "submission_id": "sub_20250618_034414_xyz789",
                "submitter_email": "test@example.com",
                "answers": [
                    {
                        "question_id": "q1",
                        "question_type": "text",
                        "value": "João Silva"
                    }
                ]
            },
            "delivery_id": "del_uuid_here",
            "source": "formerr_brunov7_beast_mode"
        }
    }