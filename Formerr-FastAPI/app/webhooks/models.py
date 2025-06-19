from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum

class WebhookEvent(str, Enum):
    SUBMISSION_CREATED = "submission.created"
    SUBMISSION_UPDATED = "submission.updated"
    FORM_CREATED = "form.created"
    FORM_UPDATED = "form.updated"
    FORM_DELETED = "form.deleted"
    USER_REGISTERED = "user.registered"

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[WebhookEvent]
    secret: Optional[str] = None
    active: bool = True

class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[WebhookEvent]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None

class WebhookResponse(BaseModel):
    id: str
    form_id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    last_triggered: Optional[str]
    failure_count: int