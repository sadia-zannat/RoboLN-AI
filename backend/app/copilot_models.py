"""Durable guided assembly. Completion is user-reported, never hardware certification."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, LargeBinary, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import uid, now


class Equipment(Base):
    __tablename__ = 'build_equipment'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(120))
    manufacturer: Mapped[str] = mapped_column(String(120), default='')
    model: Mapped[str] = mapped_column(String(120), default='')
    category: Mapped[str] = mapped_column(String(40), default='other')
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(String(2000), default='')
    known_specs: Mapped[str] = mapped_column(String(3000), default='')
    unknown_specs: Mapped[str] = mapped_column(String(2000), default='')
    proposed_function: Mapped[str] = mapped_column(String(1000), default='')
    status: Mapped[str] = mapped_column(String(24), default='USER_REPORTED')
    bom_component_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BuildPlan(Base):
    __tablename__ = 'build_plans'
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    origin: Mapped[str] = mapped_column(String(40), default='PROJECT_TEMPLATE')
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BuildStep(Base):
    __tablename__ = 'build_steps'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('build_plans.project_id', ondelete='CASCADE'), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    objective: Mapped[str] = mapped_column(String(180))
    instruction: Mapped[str] = mapped_column(String(3000))
    component_ids: Mapped[list] = mapped_column(JSON, default=list)
    checks: Mapped[list] = mapped_column(JSON, default=list)
    mistakes: Mapped[list] = mapped_column(JSON, default=list)
    safety: Mapped[str] = mapped_column(String(1500), default='')
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('project_id', 'ordinal'),)


class BuildSession(Base):
    __tablename__ = 'build_sessions'
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    current_step_id: Mapped[str | None] = mapped_column(ForeignKey('build_steps.id', ondelete='SET NULL'), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='NOT_STARTED')
    experience: Mapped[str] = mapped_column(String(12), default='beginner')
    selected_component_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    unresolved_issues: Mapped[list] = mapped_column(JSON, default=list)
    workspace_revision: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class StepProgress(Base):
    __tablename__ = 'build_step_progress'
    step_id: Mapped[str] = mapped_column(ForeignKey('build_steps.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default='NOT_STARTED')
    notes: Mapped[str] = mapped_column(String(4000), default='')
    checks_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BuildMedia(Base):
    __tablename__ = 'build_media'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    step_id: Mapped[str | None] = mapped_column(ForeignKey('build_steps.id', ondelete='SET NULL'), nullable=True)
    equipment_id: Mapped[str | None] = mapped_column(ForeignKey('build_equipment.id', ondelete='CASCADE'), nullable=True)
    filename: Mapped[str] = mapped_column(String(180))
    image: Mapped[bytes] = mapped_column(LargeBinary)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BuildCheckpoint(Base):
    __tablename__ = 'build_checkpoints'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
