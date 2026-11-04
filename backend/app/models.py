from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)
def as_utc(value):
    return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)).isoformat()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), default='')
    password_hash: Mapped[str] = mapped_column(Text)
    theme: Mapped[str] = mapped_column(String(12), default='system')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(2000), default='')
    goal: Mapped[str] = mapped_column(String(1000), default='')
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    context_version: Mapped[int] = mapped_column(Integer, default=1)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    memberships: Mapped[list['Membership']] = relationship('Membership', cascade='all, delete-orphan', passive_deletes=True)

class Membership(Base):
    __tablename__ = 'memberships'
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role: Mapped[str] = mapped_column(String(12))
    __table_args__ = (UniqueConstraint('project_id','user_id'),)

class HardwareProfile(Base):
    __tablename__ = 'hardware_profiles'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), unique=True)
    device_class: Mapped[str] = mapped_column(String(12), default='OTHER')
    board_model: Mapped[str] = mapped_column(String(160), default='')
    board_revision: Mapped[str] = mapped_column(String(100), default='')
    profile_review_state: Mapped[str] = mapped_column(String(24), default='REVIEW_REQUIRED')
    pin_map: Mapped[dict] = mapped_column(JSON, default=dict)
    sensor_inventory: Mapped[list] = mapped_column(JSON, default=list)
    source_revision_ids: Mapped[list] = mapped_column(JSON, default=list)

class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    draft: Mapped[str] = mapped_column(String(8000), default='')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('project_id','user_id'),)

class Consent(Base):
    __tablename__ = 'consents'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(70))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class LoginThrottle(Base):
    __tablename__ = 'login_throttles'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    last_failure: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class EngineeringPlan(Base):
    __tablename__ = 'engineering_plans'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    revision: Mapped[int] = mapped_column(Integer)
    context_version: Mapped[int] = mapped_column(Integer)
    family: Mapped[str] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(24), default='DRAFT')
    document: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('project_id','revision'),)

# Register complete metadata for Alembic and isolated test databases.
from . import workbench_models  # noqa: E402,F401

from . import industrial_models  # noqa: E402,F401
from . import copilot_models  # noqa: E402,F401
