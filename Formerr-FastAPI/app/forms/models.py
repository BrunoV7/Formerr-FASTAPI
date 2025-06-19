from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    RATING = "rating"
    DATE = "date"
    FILE = "file"

class QuestionBase(BaseModel):
    id: str
    type: QuestionType
    title: str
    required: bool = False
    placeholder: Optional[str] = None
    description: Optional[str] = None
    section_id: Optional[str] = None

class QuestionOption(BaseModel):
    id: str
    label: str
    value: str

class Question(QuestionBase):
    options: Optional[List[QuestionOption]] = None
    validation: Optional[Dict[str, Any]] = None
    order: int = 0

class FormSection(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    order: int = 0

class FormSettings(BaseModel):
    thank_you_message: str = "Obrigado por preencher o formulário!"
    show_progress_bar: bool = True
    allow_multiple_submissions: bool = True
    require_login: bool = False
    collect_email: bool = True
    redirect_url: Optional[str] = None

class FormBase(BaseModel):
    title: str
    description: Optional[str] = None
    public: bool = True

class FormCreate(FormBase):
    questions: List[Question] = []
    sections: List[FormSection] = []
    settings: FormSettings = FormSettings()

class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    public: Optional[bool] = None
    questions: Optional[List[Question]] = None
    sections: Optional[List[FormSection]] = None
    settings: Optional[FormSettings] = None

class Form(FormBase):
    id: str
    owner_id: int
    owner_username: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[Question] = []
    sections: List[FormSection] = []
    settings: FormSettings
    submission_count: int = 0
    last_submission: Optional[datetime] = None

class FormSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    public: bool
    created_at: datetime
    submission_count: int
    last_submission: Optional[datetime] = None

# Submission models
class SubmissionAnswer(BaseModel):
    question_id: str
    question_type: QuestionType
    value: Union[str, int, float, List[str], bool]

class SubmissionCreate(BaseModel):
    answers: List[SubmissionAnswer]
    submitter_email: Optional[str] = None
    submitter_name: Optional[str] = None

class Submission(BaseModel):
    id: str
    form_id: str
    answers: List[SubmissionAnswer]
    submitted_at: datetime
    submitter_email: Optional[str] = None
    submitter_name: Optional[str] = None
    ip_hash: Optional[str] = None