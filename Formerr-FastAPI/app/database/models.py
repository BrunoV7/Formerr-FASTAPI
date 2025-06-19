from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database.connection import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from app.auth.models import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    avatar_url = Column(Text)
    github_url = Column(Text)

    # 🔥 BEAST MODE: Advanced Auth
    role = Column(SQLEnum(UserRole), default=UserRole.FREE, nullable=False)
    subscription_expires = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Usage tracking
    monthly_submissions_used = Column(Integer, default=0)
    monthly_reset_date = Column(DateTime, default=datetime.utcnow)

    # Team features (Enterprise)
    team_id = Column(String(255), nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    # Relationships
    forms = relationship("Form", back_populates="owner", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Settings
    settings = Column(JSONB, default=dict)

    # Limits
    max_members = Column(Integer, default=10)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(255), primary_key=True, index=True)
    form_id = Column(String(255), ForeignKey("forms.id", ondelete="CASCADE"))

    # Webhook config
    url = Column(Text, nullable=False)
    events = Column(JSONB, default=list)  # ['submission.created', 'form.updated']
    secret = Column(String(255), nullable=True)

    # Status
    active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    form = relationship("Form")

class Form(Base):
    __tablename__ = "forms"

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(500), index=True, nullable=False)
    description = Column(Text, nullable=True)
    public = Column(Boolean, default=True, nullable=False)

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # JSON fields (usando JSONB do PostgreSQL para performance)
    questions = Column(JSONB, default=list)
    sections = Column(JSONB, default=list)
    settings = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Stats
    submission_count = Column(Integer, default=0)
    last_submission = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)

    # Relationships
    owner = relationship("User", back_populates="forms")
    submissions = relationship("Submission", back_populates="form", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(255), primary_key=True, index=True)
    form_id = Column(String(255), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False)

    # Submission data (JSONB para queries rápidas)
    answers = Column(JSONB, nullable=False)

    # Submitter info (opcional)
    submitter_email = Column(String(255), nullable=True)
    submitter_name = Column(String(255), nullable=True)
    submitter_ip_hash = Column(String(64), nullable=True)

    # User reference (se logado)
    submitter_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    form = relationship("Form", back_populates="submissions")
    submitter_user = relationship("User")


# Analytics table para métricas
class FormAnalytics(Base):
    __tablename__ = "form_analytics"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String(255), ForeignKey("forms.id", ondelete="CASCADE"))
    event_type = Column(String(50))  # view, start, submit, abandon
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    ip_hash = Column(String(64), nullable=True)

    # Relationships
    form = relationship("Form")