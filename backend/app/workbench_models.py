"""Persistent workbench records. Device secrets are stored only as SHA-256 hashes."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, LargeBinary, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import uid, now

class SourceDocument(Base):
    __tablename__ = 'source_documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    filename: Mapped[str] = mapped_column(String(180))
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(100))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    chunks: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('project_id','filename','version'),)

class ChatMessage(Base):
    build_step_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    equipment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    media_ids: Mapped[list] = mapped_column(JSON, default=list, server_default='[]')
    intent: Mapped[str] = mapped_column(String(20), default='question', server_default='question')
    selected_component_id:Mapped[str|None]=mapped_column(String(60),nullable=True)
    __tablename__ = 'chat_messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))
    provider_id: Mapped[str] = mapped_column(String(200))
    context_version: Mapped[int] = mapped_column(Integer)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    image_included: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class WorkbenchState(Base):
    __tablename__ = 'workbench_states'
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class WorkbenchRevision(Base):
    __tablename__ = 'workbench_revisions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('project_id','revision'),)

class Observation(Base):
    __tablename__ = 'observations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    title: Mapped[str] = mapped_column(String(160))
    notes: Mapped[str] = mapped_column(String(4000), default='')
    state: Mapped[str] = mapped_column(String(12), default='UNKNOWN')
    component_id: Mapped[str] = mapped_column(String(60), default='')
    method: Mapped[str] = mapped_column(String(32), default='USER_OBSERVATION')
    image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Device(Base):
    __tablename__ = 'devices'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    adapter: Mapped[str] = mapped_column(String(24))
    mode: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Telemetry(Base):
    __tablename__ = 'telemetry'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    device_id: Mapped[str] = mapped_column(ForeignKey('devices.id', ondelete='CASCADE'), index=True)
    packet_id: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    measurements: Mapped[list] = mapped_column(JSON)
    event: Mapped[str] = mapped_column(String(500), default='')
    __table_args__ = (UniqueConstraint('device_id','packet_id'), Index('ix_telemetry_device_time','device_id','observed_at'))

class ControlRequest(Base):
    __tablename__ = 'control_requests'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey('devices.id', ondelete='CASCADE'))
    requested_by: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    action: Mapped[str] = mapped_column(String(24))
    reason: Mapped[str] = mapped_column(String(1000))
    context_version: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(24), default='PENDING')
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
