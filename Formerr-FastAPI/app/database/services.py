from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_
from datetime import datetime
import uuid

from app.database.models import User, Form, Submission, FormAnalytics
from app.forms.models import FormCreate, FormUpdate, Form as FormSchema
from app.database.connection import get_db


class UserService:
    """Service para operações com usuários"""

    @staticmethod
    async def get_or_create_user(db: AsyncSession, github_data: Dict[str, Any]) -> User:
        """Busca ou cria usuário baseado nos dados do GitHub"""
        # Buscar usuário existente
        result = await db.execute(
            select(User).where(User.github_id == github_data["github_id"])
        )
        user = result.scalar_one_or_none()

        if user:
            # Atualizar dados do usuário existente
            user.name = github_data.get("name")
            user.email = github_data.get("email")
            user.avatar_url = github_data.get("avatar_url")
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        else:
            # Criar novo usuário
            user = User(
                github_id=github_data["github_id"],
                username=github_data["username"],
                name=github_data.get("name"),
                email=github_data.get("email"),
                avatar_url=github_data.get("avatar_url"),
                github_url=github_data.get("github_url"),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user


class FormsService:
    """Service para operações com formulários"""

    @staticmethod
    def generate_form_id() -> str:
        """Gera ID único para formulário"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"form_{timestamp}_{unique_id}"

    @staticmethod
    async def create_form(db: AsyncSession, form_data: FormCreate, owner_id: int) -> Form:
        """Cria novo formulário"""
        form_id = FormsService.generate_form_id()

        # Processar sections e questions
        sections = form_data.sections or []
        questions = form_data.questions or []

        # Auto-criar seção padrão se necessário
        if not sections and questions:
            sections = [{
                "id": "default_section",
                "title": "Perguntas",
                "description": "",
                "order": 0
            }]

        # Converter Pydantic models para dict
        questions_dict = [q.dict() for q in questions]
        sections_dict = [s.dict() for s in sections]
        settings_dict = form_data.settings.dict()

        # Criar objeto Form
        form = Form(
            id=form_id,
            title=form_data.title,
            description=form_data.description,
            public=form_data.public,
            owner_id=owner_id,
            questions=questions_dict,
            sections=sections_dict,
            settings=settings_dict,
            created_at=datetime.utcnow()
        )

        db.add(form)
        await db.commit()
        await db.refresh(form)

        return form

    @staticmethod
    async def get_user_forms(db: AsyncSession, owner_id: int, limit: int = 50) -> List[Form]:
        """Lista formulários do usuário"""
        result = await db.execute(
            select(Form)
            .where(Form.owner_id == owner_id)
            .order_by(Form.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_form_by_id(db: AsyncSession, form_id: str, owner_id: Optional[int] = None) -> Optional[Form]:
        """Busca formulário por ID"""
        query = select(Form).where(Form.id == form_id)

        if owner_id is not None:
            query = query.where(Form.owner_id == owner_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_public_form(db: AsyncSession, form_id: str) -> Optional[Form]:
        """Busca formulário público"""
        result = await db.execute(
            select(Form)
            .options(selectinload(Form.owner))
            .where(and_(Form.id == form_id, Form.public == True))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_form(db: AsyncSession, form_id: str, update_data: FormUpdate, owner_id: int) -> Optional[Form]:
        """Atualiza formulário"""
        result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = result.scalar_one_or_none()

        if not form:
            return None

        # Atualizar campos fornecidos
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if field in ["questions", "sections", "settings"] and value is not None:
                # Converter Pydantic models para dict se necessário
                if hasattr(value, 'dict'):
                    value = value.dict()
                elif isinstance(value, list) and value and hasattr(value[0], 'dict'):
                    value = [item.dict() for item in value]

            setattr(form, field, value)

        form.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(form)

        return form

    @staticmethod
    async def delete_form(db: AsyncSession, form_id: str, owner_id: int) -> bool:
        """Deleta formulário"""
        result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = result.scalar_one_or_none()

        if not form:
            return False

        await db.delete(form)
        await db.commit()
        return True

    @staticmethod
    async def increment_submission_count(db: AsyncSession, form_id: str) -> None:
        """Incrementa contador de submissões"""
        result = await db.execute(
            select(Form).where(Form.id == form_id)
        )
        form = result.scalar_one_or_none()

        if form:
            form.submission_count += 1
            form.last_submission = datetime.utcnow()
            await db.commit()


class SubmissionsService:
    """Service para operações com submissões"""

    @staticmethod
    def generate_submission_id() -> str:
        """Gera ID único para submissão"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"sub_{timestamp}_{unique_id}"

    @staticmethod
    async def create_submission(
            db: AsyncSession,
            form_id: str,
            answers: List[Dict[str, Any]],
            submitter_data: Optional[Dict[str, Any]] = None
    ) -> Submission:
        """Cria nova submissão COM WEBHOOK TRIGGER"""
        submission_id = SubmissionsService.generate_submission_id()

        # Converter answers para formato JSON
        answers_dict = [answer.dict() if hasattr(answer, 'dict') else answer for answer in answers]

        submission = Submission(
            id=submission_id,
            form_id=form_id,
            answers=answers_dict,
            submitter_email=submitter_data.get("email") if submitter_data else None,
            submitter_name=submitter_data.get("name") if submitter_data else None,
            submitter_ip_hash=submitter_data.get("ip_hash") if submitter_data else None,
            submitter_user_id=submitter_data.get("user_id") if submitter_data else None,
            submitted_at=datetime.utcnow()
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        # Incrementar contador no formulário
        await FormsService.increment_submission_count(db, form_id)

        # 🔥 BEAST MODE: Disparar webhooks
        from app.webhooks.service import webhook_service
        from app.webhooks.models import WebhookEvent

        webhook_payload = {
            "submission_id": submission.id,
            "submitter_email": submission.submitter_email,
            "submitter_name": submission.submitter_name,
            "answers": submission.answers,
            "submitted_at": submission.submitted_at.isoformat(),
            "total_answers": len(submission.answers)
        }

        # Disparar webhooks em background (não bloquear resposta)
        try:
            await webhook_service.trigger_webhooks(
                db=db,
                form_id=form_id,
                event=WebhookEvent.SUBMISSION_CREATED,
                payload=webhook_payload
            )
        except Exception as e:
            print(f"🚨 Erro ao disparar webhooks: {e}")
            # Não falhar a submissão por causa de webhook

        return submission

    @staticmethod
    async def get_form_submissions(
            db: AsyncSession,
            form_id: str,
            owner_id: int,
            limit: int = 100
    ) -> List[Submission]:
        """Lista submissões de um formulário"""
        # Verificar se o usuário é dono do formulário
        form_result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = form_result.scalar_one_or_none()

        if not form:
            return []

        result = await db.execute(
            select(Submission)
            .where(Submission.form_id == form_id)
            .order_by(Submission.submitted_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_submission_stats(db: AsyncSession, form_id: str, owner_id: int) -> Dict[str, Any]:
        """Estatísticas de submissões"""
        # Verificar ownership
        form_result = await db.execute(
            select(Form).where(and_(Form.id == form_id, Form.owner_id == owner_id))
        )
        form = form_result.scalar_one_or_none()

        if not form:
            return {}

        # Contar submissões
        total_result = await db.execute(
            select(func.count(Submission.id)).where(Submission.form_id == form_id)
        )
        total_submissions = total_result.scalar()

        # Submissões por dia (últimos 7 dias)
        # TODO: Implementar query mais complexa para estatísticas

        return {
            "form_id": form_id,
            "total_submissions": total_submissions,
            "last_submission": form.last_submission,
            "submission_rate": "TODO: calcular taxa"
        }


# Instâncias dos services
user_service = UserService()
forms_service = FormsService()
submissions_service = SubmissionsService()