from typing import List, Dict, Any, Optional
from datetime import datetime
from app.forms.models import Form, FormCreate, FormUpdate, FormSummary, Question, FormSection


class FormsService:
    """Service layer para lógica de negócio dos formulários"""

    def __init__(self):
        # TODO: Implementar database connection
        # Por enquanto, simulando com dados em memória
        self._forms_storage: Dict[str, Dict[str, Any]] = {}

    def generate_form_id(self) -> str:
        """Gera ID único para formulário"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        return f"form_{timestamp}"

    def create_form(self, form_data: FormCreate, owner_id: int, owner_username: str) -> Form:
        """Cria novo formulário"""
        form_id = self.generate_form_id()

        # Processar sections e questions
        sections = form_data.sections or []
        questions = form_data.questions or []

        # Auto-criar seção padrão se não houver
        if not sections and questions:
            sections = [FormSection(
                id="default_section",
                title="Perguntas",
                description="",
                order=0
            )]

        # Definir section_id padrão para questions sem seção
        for question in questions:
            if not question.section_id and sections:
                question.section_id = sections[0].id

        # Criar objeto Form
        form = Form(
            id=form_id,
            title=form_data.title,
            description=form_data.description,
            public=form_data.public,
            owner_id=owner_id,
            owner_username=owner_username,
            created_at=datetime.utcnow(),
            questions=questions,
            sections=sections,
            settings=form_data.settings,
            submission_count=0
        )

        # Salvar em storage (simulado)
        self._forms_storage[form_id] = form.dict()

        return form

    def get_user_forms(self, owner_id: int) -> List[FormSummary]:
        """Lista formulários do usuário"""
        user_forms = []

        for form_data in self._forms_storage.values():
            if form_data["owner_id"] == owner_id:
                user_forms.append(FormSummary(**form_data))

        # Ordenar por data de criação (mais recente primeiro)
        user_forms.sort(key=lambda x: x.created_at, reverse=True)

        return user_forms

    def get_form_by_id(self, form_id: str, owner_id: Optional[int] = None) -> Optional[Form]:
        """Busca formulário por ID"""
        form_data = self._forms_storage.get(form_id)

        if not form_data:
            return None

        # Se owner_id fornecido, verificar ownership
        if owner_id is not None and form_data["owner_id"] != owner_id:
            return None

        return Form(**form_data)

    def get_public_form(self, form_id: str) -> Optional[Form]:
        """Busca formulário público"""
        form_data = self._forms_storage.get(form_id)

        if not form_data or not form_data.get("public", False):
            return None

        return Form(**form_data)

    def update_form(self, form_id: str, update_data: FormUpdate, owner_id: int) -> Optional[Form]:
        """Atualiza formulário"""
        form_data = self._forms_storage.get(form_id)

        if not form_data or form_data["owner_id"] != owner_id:
            return None

        # Atualizar campos fornecidos
        update_dict = update_data.dict(exclude_unset=True)
        form_data.update(update_dict)
        form_data["updated_at"] = datetime.utcnow()

        # Salvar atualização
        self._forms_storage[form_id] = form_data

        return Form(**form_data)

    def delete_form(self, form_id: str, owner_id: int) -> bool:
        """Deleta formulário"""
        form_data = self._forms_storage.get(form_id)

        if not form_data or form_data["owner_id"] != owner_id:
            return False

        del self._forms_storage[form_id]
        return True

    def increment_submission_count(self, form_id: str) -> None:
        """Incrementa contador de submissões"""
        if form_id in self._forms_storage:
            self._forms_storage[form_id]["submission_count"] += 1
            self._forms_storage[form_id]["last_submission"] = datetime.utcnow()


# Singleton instance
forms_service = FormsService()