import httpx
import hmac
import hashlib
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.database.models import Webhook, Form
from app.webhooks.models import WebhookCreate, WebhookUpdate, WebhookEvent


class WebhookService:
    """Beast Mode Webhook Service"""

    @staticmethod
    def generate_webhook_id() -> str:
        """Gera ID único para webhook"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"webhook_{timestamp}_{unique_id}"

    @staticmethod
    def generate_secret() -> str:
        """Gera secret para webhook"""
        return f"whsec_{uuid.uuid4().hex[:32]}"

    @staticmethod
    def create_signature(payload: str, secret: str) -> str:
        """Cria assinatura HMAC-SHA256"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    async def create_webhook(
            db: AsyncSession,
            form_id: str,
            webhook_data: WebhookCreate,
            owner_id: int
    ) -> Optional[Webhook]:
        """Cria novo webhook"""

        # Verificar se o form existe e pertence ao usuário
        form_result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = form_result.scalar_one_or_none()

        if not form:
            return None

        webhook_id = WebhookService.generate_webhook_id()
        secret = webhook_data.secret or WebhookService.generate_secret()

        webhook = Webhook(
            id=webhook_id,
            form_id=form_id,
            url=str(webhook_data.url),
            events=[event.value for event in webhook_data.events],
            secret=secret,
            active=webhook_data.active,
            created_at=datetime.utcnow()
        )

        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)

        return webhook

    @staticmethod
    async def get_form_webhooks(
            db: AsyncSession,
            form_id: str,
            owner_id: int
    ) -> List[Webhook]:
        """Lista webhooks de um formulário"""

        # Verificar ownership
        form_result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = form_result.scalar_one_or_none()

        if not form:
            return []

        result = await db.execute(
            select(Webhook).where(Webhook.form_id == form_id)
        )
        return result.scalars().all()

    @staticmethod
    async def trigger_webhooks(
            db: AsyncSession,
            form_id: str,
            event: WebhookEvent,
            payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Dispara webhooks para um evento"""

        # Buscar webhooks ativos para este form e evento
        result = await db.execute(
            select(Webhook).where(
                and_(
                    Webhook.form_id == form_id,
                    Webhook.active == True,
                    Webhook.events.contains([event.value])
                )
            )
        )
        webhooks = result.scalars().all()

        if not webhooks:
            return []

        # Preparar payload completo
        webhook_payload = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "form_id": form_id,
            "data": payload,
            "delivery_id": str(uuid.uuid4()),
            "source": "formerr_brunov7_beast_mode"
        }

        results = []

        for webhook in webhooks:
            try:
                result = await WebhookService._send_webhook(webhook, webhook_payload)
                results.append(result)

                # Atualizar webhook stats
                webhook.last_triggered = datetime.utcnow()
                if not result["success"]:
                    webhook.failure_count += 1
                else:
                    webhook.failure_count = 0  # Reset on success

            except Exception as e:
                results.append({
                    "webhook_id": webhook.id,
                    "success": False,
                    "error": str(e),
                    "url": webhook.url
                })
                webhook.failure_count += 1

        await db.commit()
        return results

    @staticmethod
    async def _send_webhook(webhook: Webhook, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Envia webhook HTTP request"""

        payload_str = json.dumps(payload, ensure_ascii=False)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Formerr-Webhooks/1.0 (BrunoV7)",
            "X-Formerr-Event": payload["event"],
            "X-Formerr-Delivery": payload["delivery_id"],
            "X-Formerr-Timestamp": payload["timestamp"]
        }

        # Adicionar assinatura se tem secret
        if webhook.secret:
            signature = WebhookService.create_signature(payload_str, webhook.secret)
            headers["X-Formerr-Signature"] = signature

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    webhook.url,
                    content=payload_str,
                    headers=headers
                )

                return {
                    "webhook_id": webhook.id,
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                    "url": webhook.url,
                    "delivery_id": payload["delivery_id"]
                }

            except httpx.TimeoutException:
                return {
                    "webhook_id": webhook.id,
                    "success": False,
                    "error": "timeout",
                    "url": webhook.url
                }
            except Exception as e:
                return {
                    "webhook_id": webhook.id,
                    "success": False,
                    "error": str(e),
                    "url": webhook.url
                }

    @staticmethod
    async def test_webhook(
            db: AsyncSession,
            webhook_id: str,
            owner_id: int
    ) -> Dict[str, Any]:
        """Testa webhook com payload de exemplo"""

        # Buscar webhook
        result = await db.execute(
            select(Webhook)
            .join(Form)
            .where(
                and_(
                    Webhook.id == webhook_id,
                    Form.owner_id == owner_id
                )
            )
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        # Payload de teste
        test_payload = {
            "event": "webhook.test",
            "timestamp": datetime.utcnow().isoformat(),
            "form_id": webhook.form_id,
            "data": {
                "test": True,
                "message": "This is a test webhook from Formerr Beast Mode",
                "brunov7_says": "🚀 WEBHOOK TEST SUCCESSFUL! 🚀"
            },
            "delivery_id": str(uuid.uuid4()),
            "source": "formerr_test_brunov7"
        }

        result = await WebhookService._send_webhook(webhook, test_payload)

        # Atualizar stats
        webhook.last_triggered = datetime.utcnow()
        if not result["success"]:
            webhook.failure_count += 1

        await db.commit()

        return result


# Instance
webhook_service = WebhookService()