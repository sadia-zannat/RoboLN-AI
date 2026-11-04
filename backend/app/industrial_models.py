"""Project-scoped industrial workspace records. No physical command executor."""
from datetime import datetime
from sqlalchemy import String,Integer,Float,DateTime,ForeignKey,JSON,UniqueConstraint,Index
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
from .models import uid,now
class ComponentMapping(Base):
    __tablename__='component_mappings'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    project_id:Mapped[str]=mapped_column(ForeignKey('projects.id',ondelete='CASCADE'),index=True)
    device_id:Mapped[str]=mapped_column(ForeignKey('devices.id',ondelete='CASCADE'),index=True)
    component_id:Mapped[str]=mapped_column(String(60))
    measurement:Mapped[str]=mapped_column(String(60))
    unit:Mapped[str]=mapped_column(String(24))
    channel:Mapped[str]=mapped_column(String(24),default='VALUE_ONLY')
    stale_after:Mapped[int]=mapped_column(Integer,default=60)
    lower:Mapped[float|None]=mapped_column(Float,nullable=True)
    upper:Mapped[float|None]=mapped_column(Float,nullable=True)
    __table_args__=(UniqueConstraint('device_id','measurement'),)
class SensorReading(Base):
    __tablename__='sensor_readings'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    telemetry_id:Mapped[str]=mapped_column(ForeignKey('telemetry.id',ondelete='CASCADE'),index=True)
    device_id:Mapped[str]=mapped_column(ForeignKey('devices.id',ondelete='CASCADE'))
    name:Mapped[str]=mapped_column(String(60))
    value:Mapped[float]=mapped_column(Float)
    unit:Mapped[str]=mapped_column(String(24))
    observed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    received_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    __table_args__=(Index('ix_sensor_stream_time','device_id','name','observed_at'),UniqueConstraint('telemetry_id','name'))
class SimulationRun(Base):
    __tablename__='simulation_runs'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    project_id:Mapped[str]=mapped_column(ForeignKey('projects.id',ondelete='CASCADE'),index=True)
    author_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'))
    workspace_revision:Mapped[int]=mapped_column(Integer)
    parameters:Mapped[dict]=mapped_column(JSON)
    trace:Mapped[list]=mapped_column(JSON)
    events:Mapped[list]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class ChangeProposal(Base):
    __tablename__='change_proposals'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    project_id:Mapped[str]=mapped_column(ForeignKey('projects.id',ondelete='CASCADE'),index=True)
    author_id:Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'))
    message_id:Mapped[str]=mapped_column(ForeignKey('chat_messages.id',ondelete='CASCADE'))
    component_id:Mapped[str]=mapped_column(String(60))
    workspace_revision:Mapped[int]=mapped_column(Integer)
    original:Mapped[str]=mapped_column(String(1000))
    proposed:Mapped[str]=mapped_column(String(1000))
    reason:Mapped[str]=mapped_column(String(1000))
    state:Mapped[str]=mapped_column(String(24),default='PENDING_REVIEW')
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
