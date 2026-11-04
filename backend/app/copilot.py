"""Project-scoped guided builds, inventory, media and per-user durable checkpoints."""
import base64
import json
import re
import hashlib
from pathlib import PurePosixPath
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, defer
from .api import authorized, audit
from .db import get_db
from .models import User, now, as_utc
from .security import current_user, csrf_guard
from .sources import image_bytes
from .workbench_models import ChatMessage, SourceDocument, WorkbenchState
from .copilot_models import Equipment, BuildPlan, BuildStep, BuildSession, StepProgress, BuildMedia, BuildCheckpoint

router = APIRouter(prefix='/api/projects/{pid}')
write = [Depends(csrf_guard)]
STATES = ['NOT_STARTED', 'IN_PROGRESS', 'WAITING_FOR_EVIDENCE', 'NEEDS_MORE_EVIDENCE', 'NEEDS_REVIEW', 'USER_CONFIRMED', 'COMPLETED', 'BLOCKED']

def scoped(db, model, pid, identifier, label):
    row = db.get(model, identifier)
    if not row or row.project_id != pid:
        raise HTTPException(404, label + ' not found')
    return row

def part_ids(db, pid):
    w = db.get(WorkbenchState, pid)
    return {p['id'] for p in (w.data.get('parts', []) if w else [])}

def check_parts(db, pid, ids):
    if any(i not in part_ids(db, pid) for i in ids):
        raise HTTPException(422, 'Component references must belong to this saved assembly')

def media_info(m):
    return {'id': m.id, 'filename': m.filename, 'step_id': m.step_id, 'equipment_id': m.equipment_id,
        'sha256': m.sha256, 'media_type': 'image/jpeg', 'created_at': as_utc(m.created_at), 'origin': 'USER_REPORTED'}

def equipment_info(e, photos):
    return {k: getattr(e, k) for k in ['id', 'name', 'manufacturer', 'model', 'category', 'quantity', 'description', 'known_specs', 'unknown_specs', 'proposed_function', 'status', 'bom_component_id', 'source_ids', 'revision']} | {'photos': [media_info(m) for m in photos if m.equipment_id == e.id]}

def step_info(s):
    return {k: getattr(s, k) for k in ['id', 'ordinal', 'objective', 'instruction', 'component_ids', 'checks', 'mistakes', 'safety', 'evidence_required']}

def progress_info(p):
    return {'status': p.status, 'notes': p.notes, 'checks_confirmed': p.checks_confirmed,
        'confirmed_at': as_utc(p.confirmed_at) if p.confirmed_at else None, 'completed_at': as_utc(p.completed_at) if p.completed_at else None,
        'provenance': 'USER_REPORTED', 'physical_verification': 'NOT_VERIFIED'} if p else {'status': 'NOT_STARTED', 'notes': '', 'checks_confirmed': False, 'confirmed_at': None, 'completed_at': None, 'provenance': 'USER_REPORTED', 'physical_verification': 'NOT_VERIFIED'}

def session_info(s):
    return {'revision': s.revision, 'current_step_id': s.current_step_id, 'status': s.status, 'experience': s.experience,
        'selected_component_id': s.selected_component_id, 'unresolved_issues': s.unresolved_issues, 'workspace_revision': s.workspace_revision,
        'last_checkpoint': as_utc(s.updated_at)} if s else {'revision': 0, 'current_step_id': None, 'status': 'NOT_STARTED', 'experience': 'beginner', 'selected_component_id': None, 'unresolved_issues': [], 'workspace_revision': 0, 'last_checkpoint': None}

def inventory(db, pid):
    equipment = db.scalars(select(Equipment).where(Equipment.project_id == pid).order_by(Equipment.created_at)).all()
    media = db.scalars(select(BuildMedia).options(defer(BuildMedia.image)).where(BuildMedia.project_id == pid).order_by(BuildMedia.created_at.desc())).all()
    w = db.get(WorkbenchState, pid)
    missing = []
    for p in w.data.get('parts', []) if w else []:
        available = sum(e.quantity for e in equipment if e.bom_component_id == p['id'])
        if available < p.get('quantity', 1):
            missing.append({'component_id': p['id'], 'name': p['name'], 'required': p.get('quantity', 1), 'available': available, 'missing': p.get('quantity', 1) - available})
    return equipment, media, missing

@router.get('/build')
def get_build(pid: str, db: Session = Depends(get_db), u: User = Depends(current_user)):
    p, _ = authorized(db, pid, u)
    plan = db.get(BuildPlan, pid)
    steps = db.scalars(select(BuildStep).where(BuildStep.project_id == pid).order_by(BuildStep.ordinal)).all()
    session = db.get(BuildSession, (pid, u.id))
    progress = {r.step_id: r for r in db.scalars(select(StepProgress).join(BuildStep, BuildStep.id == StepProgress.step_id).where(BuildStep.project_id == pid, StepProgress.user_id == u.id))}
    equipment, media, missing = inventory(db, pid)
    checkpoints = db.scalars(select(BuildCheckpoint).where(BuildCheckpoint.project_id == pid, BuildCheckpoint.user_id == u.id).order_by(BuildCheckpoint.created_at.desc()).limit(10)).all()
    messages = db.scalars(select(ChatMessage).where(ChatMessage.project_id == pid, ChatMessage.user_id == u.id).order_by(ChatMessage.created_at.desc(),ChatMessage.id.desc()).limit(50)).all()
    from .workbench import chat_info
    current = next((s for s in steps if session and s.id == session.current_step_id), None)
    return {'goal': p.goal, 'plan_revision': plan.revision if plan else 0, 'plan_origin': plan.origin if plan else None,
        'steps': [step_info(s) | {'progress': progress_info(progress.get(s.id))} for s in steps],
        'session': session_info(session), 'equipment': [equipment_info(e, media) for e in equipment],
        'media': [media_info(m) for m in media], 'missing_parts': missing,
        'messages': [chat_info(m) for m in reversed(messages)], 'completed_steps': sum(r.status == 'COMPLETED' for r in progress.values()),
        'checkpoints': [{'id': c.id, 'created_at': as_utc(c.created_at), 'snapshot': c.snapshot} for c in checkpoints],
        'next_action': ('Build steps are user-reported complete; independent physical commissioning remains required.' if session and session.status == 'COMPLETED' else current.instruction if current else 'Add equipment and generate a guided build plan.'),
        'physical_verification': 'NOT_VERIFIED', 'states': STATES}

class EquipmentEdit(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    manufacturer: str = Field(default='', max_length=120)
    model: str = Field(default='', max_length=120)
    category: Literal['controller', 'sensor', 'motor', 'power', 'mechanical', 'camera', 'tool', 'other'] = 'other'
    quantity: int = Field(default=1, ge=1, le=1000)
    description: str = Field(default='', max_length=2000)
    known_specs: str = Field(default='', max_length=3000)
    unknown_specs: str = Field(default='', max_length=2000)
    proposed_function: str = Field(default='', max_length=1000)
    status: Literal['NOT_VERIFIED', 'USER_REPORTED', 'AI_INFERRED', 'USER_CONFIRMED'] = 'USER_REPORTED'
    bom_component_id: str | None = Field(default=None, max_length=60)
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    expected_revision: int | None = Field(default=None, ge=1)
    @field_validator('name')
    @classmethod
    def name_not_blank(cls, value):
        if not value.strip(): raise ValueError('Equipment name cannot be blank')
        return value.strip()

def validate_equipment(db, pid, payload):
    if payload.bom_component_id: check_parts(db, pid, [payload.bom_component_id])
    for sid in payload.source_ids: scoped(db, SourceDocument, pid, sid, 'Source')

@router.post('/equipment', dependencies=write, status_code=201)
def add_equipment(pid: str, payload: EquipmentEdit, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True)
    validate_equipment(db, pid, payload)
    if (db.scalar(select(func.count()).select_from(Equipment).where(Equipment.project_id == pid)) or 0) >= 100: raise HTTPException(409, 'Inventory limit is 100 equipment records')
    e = Equipment(project_id=pid, author_id=u.id, **payload.model_dump(exclude={'expected_revision'}))
    db.add(e); audit(db, 'equipment.created', u.id, pid); db.commit()
    return equipment_info(e, [])

@router.put('/equipment/{eid}', dependencies=write)
def edit_equipment(pid: str, eid: str, payload: EquipmentEdit, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True); e = scoped(db, Equipment, pid, eid, 'Equipment')
    validate_equipment(db, pid, payload)
    result = db.execute(update(Equipment).where(Equipment.id == e.id, Equipment.revision == payload.expected_revision).values(**payload.model_dump(exclude={'expected_revision'}), revision=Equipment.revision + 1))
    if result.rowcount != 1: db.rollback(); raise HTTPException(409, 'Inventory changed. Reload before saving.')
    audit(db, 'equipment.corrected', u.id, pid); db.commit(); db.refresh(e)
    photos = db.scalars(select(BuildMedia).options(defer(BuildMedia.image)).where(BuildMedia.equipment_id == eid)).all()
    return equipment_info(e, photos)

@router.delete('/equipment/{eid}', dependencies=write, status_code=204)
def remove_equipment(pid: str, eid: str, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True); e = scoped(db, Equipment, pid, eid, 'Equipment')
    db.execute(delete(BuildMedia).where(BuildMedia.equipment_id == eid)); db.delete(e)
    audit(db, 'equipment.deleted', u.id, pid); db.commit()

@router.post('/build/media', dependencies=write, status_code=201)
async def upload_media(pid: str, file: UploadFile = File(...), storage_consent: bool = Form(False), step_id: str | None = Form(None), equipment_id: str | None = Form(None), db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True)
    if not storage_consent: raise HTTPException(403, 'Confirm storing this image and sharing it with project members')
    if step_id: scoped(db, BuildStep, pid, step_id, 'Build step')
    if equipment_id: scoped(db, Equipment, pid, equipment_id, 'Equipment')
    if bool(step_id) == bool(equipment_id): raise HTTPException(422, 'Link the photo to exactly one equipment record or build step')
    if (db.scalar(select(func.count()).select_from(BuildMedia).where(BuildMedia.project_id == pid)) or 0) >= 100: raise HTTPException(409, 'Project photo limit is 100; delete unused photos first')
    filename = PurePosixPath((file.filename or 'photo').replace('\\', '/')).name
    if not filename or len(filename) > 180 or any(ord(c) < 32 for c in filename): raise HTTPException(422, 'Invalid filename')
    mime = file.content_type
    raw = await file.read(3 * 1024 * 1024 + 1); await file.close()
    if mime not in ('image/png', 'image/jpeg', 'image/webp'): raise HTTPException(415, 'Choose PNG, JPEG or WebP')
    if not raw or len(raw) > 3 * 1024 * 1024: raise HTTPException(413, 'Photo must be 1 byte to 3 MiB')
    normalized = image_bytes('data:' + mime + ';base64,' + base64.b64encode(raw).decode())
    m = BuildMedia(project_id=pid, author_id=u.id, step_id=step_id, equipment_id=equipment_id, filename=filename, image=normalized, sha256=hashlib.sha256(normalized).hexdigest())
    db.add(m); audit(db, 'build.photo.saved', u.id, pid); db.commit()
    return media_info(m)

@router.get('/build/media/{mid}')
def read_media(pid: str, mid: str, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u); m = scoped(db, BuildMedia, pid, mid, 'Photo')
    return Response(m.image, media_type='image/jpeg', headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})

@router.delete('/build/media/{mid}', dependencies=write, status_code=204)
def delete_media(pid: str, mid: str, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True); m = scoped(db, BuildMedia, pid, mid, 'Photo')
    if m.step_id:
        progress = db.get(StepProgress, (m.step_id, m.author_id))
        if progress:
            progress.status = 'NEEDS_MORE_EVIDENCE'; progress.completed_at = None; progress.confirmed_at = None; progress.checks_confirmed = False
            db.execute(update(BuildSession).where(BuildSession.project_id == pid, BuildSession.user_id == m.author_id).values(status='NEEDS_MORE_EVIDENCE', revision=BuildSession.revision + 1, updated_at=now()))
    db.delete(m); audit(db, 'build.photo.deleted', u.id, pid); db.commit()

class StepSpec(BaseModel):
    objective: str = Field(min_length=3, max_length=180)
    instruction: str = Field(min_length=5, max_length=3000)
    component_ids: list[str] = Field(default_factory=list, max_length=40)
    checks: list[str] = Field(default_factory=list, max_length=12)
    mistakes: list[str] = Field(default_factory=list, max_length=12)
    safety: str = Field(default='', max_length=1500)
    evidence_required: bool = False
    @field_validator('checks', 'mistakes', 'component_ids')
    @classmethod
    def bounded_items(cls, items):
        if any(not x.strip() or len(x) > 400 for x in items): raise ValueError('List entries must contain 1–400 characters')
        return items
    @field_validator('objective', 'instruction')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Step text cannot be blank')
        return value.strip()

class PlanCreate(BaseModel):
    steps: list[StepSpec] | None = Field(default=None, min_length=1, max_length=60)
    proposal_message_id: str | None = Field(default=None,max_length=36)

class PlanProposal(BaseModel):
    consent: bool = False

@router.post('/build/plan/proposal', dependencies=write)
def propose_plan(pid: str, payload: PlanProposal, db: Session = Depends(get_db), u: User = Depends(current_user)):
    project, _ = authorized(db, pid, u, write=True)
    from .workbench import cloud_consent, rate_guard, SYSTEM, chat_info
    from .sources import retrieve
    from . import meta_ai
    cloud_consent(db,u,payload.consent)
    if meta_ai.configuration()['status']=='NOT_CONFIGURED': raise HTTPException(503,'NOT_CONFIGURED: set MODEL_API_KEY on the backend')
    equipment, photos, missing = inventory(db,pid)
    w=db.get(WorkbenchState,pid)
    refs=retrieve(db.scalars(select(SourceDocument).where(SourceDocument.project_id==pid)).all(),project.goal+' assembly build plan')
    context={'project_goal':project.goal,'equipment':[equipment_info(e,photos) for e in equipment],
        'saved_assembly':w.data if w else {},'missing_parts':missing,'untrusted_source_excerpts':refs}
    rate_guard(db,u,pid)
    result=meta_ai.infer([{'role':'developer','content':SYSTEM+'\nReturn ONLY a JSON object with a steps array of 3–12 simple English steps. Each step has objective, instruction, component_ids (use only IDs from the saved assembly), checks (string array), mistakes (string array), safety (string), evidence_required (boolean). Cover identification, unpowered preparation, visible assembly, independent checks and unresolved issues. Do not invent exact wiring or power ratings. This is a proposal for user review, never physical verification.'},
        {'role':'user','content':'UNTRUSTED PROJECT EVIDENCE:\n'+json.dumps(context,ensure_ascii=False)}])
    from pydantic import ValidationError
    try:
        parsed=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',result['answer'].strip()))
        if not isinstance(parsed,dict) or not isinstance(parsed.get('steps'),list): raise ValueError()
        draft=PlanCreate(steps=parsed['steps'])
        for step in draft.steps: check_parts(db,pid,step.component_ids)
    except (ValueError,TypeError,ValidationError,HTTPException):
        audit(db,'build.plan.proposal.failed',u.id,pid);db.commit()
        raise HTTPException(502,'Provider returned an unusable build-plan proposal. No build steps were changed. You can retry or use the project template.')
    message=ChatMessage(project_id=pid,user_id=u.id,question='Propose a guided build plan in English',answer=result['answer'],model=result['model'],provider_id=result['provider_id'],context_version=project.context_version,sources=refs,image_included=False,intent='plan_proposal',media_ids=[])
    db.add(message);audit(db,'build.plan.proposal.saved',u.id,pid);db.commit()
    return {'steps':[s.model_dump() for s in draft.steps],'message':chat_info(message),'state':'USER_REVIEW_REQUIRED'}

def template_steps(db, pid):
    w = db.get(WorkbenchState, pid)
    parts = w.data.get('parts', []) if w else []
    eq = db.scalars(select(Equipment).where(Equipment.project_id == pid)).all()
    ids = [p['id'] for p in parts]
    steps = [StepSpec(objective='Identify your available equipment', instruction='Lay out the unpowered parts. Compare each label with your saved equipment inventory and correct any unknown model before assembly.', component_ids=ids[:6], checks=['Names and quantities match the parts on your desk', 'Unknown specifications are recorded'], mistakes=['Guessing a board revision from appearance'], safety='Keep every power source disconnected.')]
    steps.append(StepSpec(objective='Review documents and the unpowered design', instruction='Open the technical references for this project. Identify mounting locations and independent checks before making connections.', checks=['Datasheets or unknown ratings are recorded', 'A qualified person will review power and wiring before energizing'], mistakes=['Treating the 3D draft or an AI photo as a verified wiring diagram'], safety='No live wiring or actuator execution is authorized.', evidence_required=True))
    targets = parts or [{'id': None, 'name': e.name} for e in eq] or [{'id': None, 'name': 'your first component'}]
    if len(targets)>57: raise HTTPException(409,'For a large inventory, save a grouped BOM or request a reviewed Meta plan before generating steps.')
    for p in targets:
        steps.append(StepSpec(objective=('Position ' + p['name'])[:180], instruction=f"With power disconnected, identify {p['name']} and place it at the reviewed mounting location. Use the 3D reference as a provisional visual guide. Photograph the visible placement and record your checks before continuing.", component_ids=[p['id']] if p['id'] else [], checks=['The part label and intended location match', 'The part is supported and cables are not strained'], mistakes=['Forcing a connector or fastener', 'Assuming a photograph proves continuity or polarity'], safety='Do not energize the assembly. Ask for independent review when a rating or connection is unknown.', evidence_required=True))
    steps.append(StepSpec(objective='Record independent checks and the next test', instruction='Record the actual independent checks, results and unresolved issues. If you have an enrolled device, inspect its labeled telemetry separately. Finishing these steps records your progress; it does not commission the hardware.', checks=['Unresolved issues are recorded', 'Physical tests have a method and result'], mistakes=['Treating simulated telemetry as physical evidence'], safety='Physical control remains HOLD_NO_EXECUTOR.', evidence_required=True))
    return steps

@router.post('/build/plan', dependencies=write, status_code=201)
def create_plan(pid: str, payload: PlanCreate, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True)
    if db.get(BuildPlan, pid): raise HTTPException(409, 'A build plan already exists. Edit its steps without replacing saved progress.')
    steps = payload.steps if payload.steps is not None else template_steps(db, pid)
    for s in steps: check_parts(db, pid, s.component_ids)
    origin='USER_AUTHORED' if payload.steps else 'PROJECT_TEMPLATE'
    if payload.proposal_message_id:
        message=scoped(db,ChatMessage,pid,payload.proposal_message_id,'Plan proposal')
        if message.user_id!=u.id or message.intent!='plan_proposal' or not payload.steps: raise HTTPException(404,'Plan proposal not found')
        origin='USER_REVIEWED_PROVIDER_PROPOSAL'
    db.add(BuildPlan(project_id=pid, author_id=u.id, origin=origin))
    try: db.flush()
    except IntegrityError: db.rollback(); raise HTTPException(409,'A build plan was created concurrently. Reload.')
    for i, s in enumerate(steps): db.add(BuildStep(project_id=pid, ordinal=i + 1, **s.model_dump()))
    audit(db, 'build.plan.created', u.id, pid)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409, 'A concurrent build plan was created. Reload.')
    return get_build(pid, db, u)

class StepEdit(StepSpec):
    expected_plan_revision: int = Field(ge=1)

@router.put('/build/steps/{sid}', dependencies=write)
def edit_step(pid: str, sid: str, payload: StepEdit, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True); step = scoped(db, BuildStep, pid, sid, 'Build step')
    check_parts(db, pid, payload.component_ids)
    result = db.execute(update(BuildPlan).where(BuildPlan.project_id == pid, BuildPlan.revision == payload.expected_plan_revision).values(revision=BuildPlan.revision + 1, updated_at=now()))
    if result.rowcount != 1: db.rollback(); raise HTTPException(409, 'Build plan changed. Reload before editing.')
    for k, v in payload.model_dump(exclude={'expected_plan_revision'}).items(): setattr(step, k, v)
    db.execute(update(StepProgress).where(StepProgress.step_id == sid).values(status='NEEDS_REVIEW', checks_confirmed=False, confirmed_at=None, completed_at=None))
    db.execute(update(BuildSession).where(BuildSession.project_id == pid).values(status='NEEDS_REVIEW', revision=BuildSession.revision + 1, updated_at=now()))
    audit(db, 'build.step.edited', u.id, pid); db.commit()
    return get_build(pid, db, u)

@router.post('/build/steps', dependencies=write, status_code=201)
def append_step(pid: str, payload: StepEdit, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True); check_parts(db, pid, payload.component_ids)
    plan = db.get(BuildPlan, pid)
    if not plan: raise HTTPException(409, 'Generate a build plan first')
    ordinal = (db.scalar(select(func.max(BuildStep.ordinal)).where(BuildStep.project_id == pid)) or 0) + 1
    if ordinal > 60: raise HTTPException(409, 'Build plan limit is 60 steps')
    result = db.execute(update(BuildPlan).where(BuildPlan.project_id == pid, BuildPlan.revision == payload.expected_plan_revision).values(revision=BuildPlan.revision + 1, updated_at=now()))
    if result.rowcount != 1: db.rollback(); raise HTTPException(409, 'Build plan changed. Reload.')
    db.add(BuildStep(project_id=pid, ordinal=ordinal, **payload.model_dump(exclude={'expected_plan_revision'})))
    db.execute(update(BuildSession).where(BuildSession.project_id == pid).values(status='NEEDS_REVIEW', revision=BuildSession.revision + 1, updated_at=now()))
    audit(db, 'build.step.appended', u.id, pid); db.commit()
    return get_build(pid, db, u)

class SessionEdit(BaseModel):
    expected_revision: int = Field(ge=0)
    action: Literal['start', 'save', 'go', 'confirm', 'complete', 'status'] = 'save'
    step_id: str | None = Field(default=None, max_length=36)
    notes: str | None = Field(default=None, max_length=4000)
    checks_confirmed: bool = False
    attestation: bool = False
    status: Literal['IN_PROGRESS', 'WAITING_FOR_EVIDENCE', 'NEEDS_MORE_EVIDENCE', 'NEEDS_REVIEW', 'BLOCKED'] | None = None
    experience: Literal['beginner', 'advanced'] | None = None
    selected_component_id: str | None = Field(default=None, max_length=60)
    unresolved_issues: list[str] | None = Field(default=None, max_length=40)
    @field_validator('unresolved_issues')
    @classmethod
    def issues_bounded(cls, items):
        if items and any(not x.strip() or len(x) > 500 for x in items): raise ValueError('Issues must contain 1–500 characters')
        return items

def checkpoint(db, pid, u, session, steps):
    progress = {s.id: progress_info(db.get(StepProgress, (s.id, u.id))) for s in steps}
    plan = db.get(BuildPlan, pid)
    snapshot = session_info(session) | {'plan_revision': plan.revision if plan else 0, 'step_progress': progress}
    db.add(BuildCheckpoint(project_id=pid, user_id=u.id, snapshot=snapshot))
    old = db.scalars(select(BuildCheckpoint.id).where(BuildCheckpoint.project_id == pid, BuildCheckpoint.user_id == u.id).order_by(BuildCheckpoint.created_at.desc()).offset(49)).all()
    if old: db.execute(delete(BuildCheckpoint).where(BuildCheckpoint.id.in_(old)))

@router.put('/build/session', dependencies=write)
def update_session(pid: str, payload: SessionEdit, db: Session = Depends(get_db), u: User = Depends(current_user)):
    authorized(db, pid, u, write=True)
    steps = db.scalars(select(BuildStep).where(BuildStep.project_id == pid).order_by(BuildStep.ordinal)).all()
    s = db.get(BuildSession, (pid, u.id))
    if not s:
        if payload.expected_revision != 0: raise HTTPException(409, 'Checkpoint changed. Reload.')
        s = BuildSession(project_id=pid, user_id=u.id, revision=0); db.add(s)
        try: db.flush()
        except IntegrityError: db.rollback(); raise HTTPException(409, 'Checkpoint created concurrently. Reload.')
    if s.revision != payload.expected_revision: raise HTTPException(409, 'Build progress changed in another tab. Reload before saving.')
    current_id = payload.step_id if payload.step_id is not None else s.current_step_id
    if payload.action == 'start' and not current_id: current_id = steps[0].id if steps else None
    step = scoped(db, BuildStep, pid, current_id, 'Build step') if current_id else None
    if payload.action in ('start', 'go', 'confirm', 'complete', 'status') and not step: raise HTTPException(409, 'Generate a build plan and select a step first')
    if payload.selected_component_id: check_parts(db, pid, [payload.selected_component_id])
    progress = db.get(StepProgress, (step.id, u.id)) if step else None
    if step and not progress:
        progress = StepProgress(step_id=step.id, user_id=u.id); db.add(progress)
        try: db.flush()
        except IntegrityError: db.rollback(); raise HTTPException(409,'Step progress changed concurrently. Reload.')
    if progress and payload.notes is not None: progress.notes = payload.notes
    if progress and payload.action == 'start' and progress.status == 'NOT_STARTED': progress.status = 'IN_PROGRESS'
    if progress and payload.action == 'confirm':
        if not payload.attestation or not payload.checks_confirmed or len(progress.notes.strip()) < 10: raise HTTPException(422, 'Confirm the checks and record what you independently observed (at least 10 characters)')
        has_photo = db.scalar(select(func.count()).select_from(BuildMedia).where(BuildMedia.project_id == pid, BuildMedia.step_id == step.id, BuildMedia.author_id == u.id)) or 0
        if step.evidence_required and not has_photo and len(progress.notes.strip()) < 20: raise HTTPException(409, 'Add a step photo or independent check notes of at least 20 characters')
        progress.status = 'USER_CONFIRMED'; progress.checks_confirmed = True; progress.confirmed_at = now(); progress.completed_at = None
    if progress and payload.action == 'complete':
        if progress.status != 'USER_CONFIRMED' or not progress.checks_confirmed: raise HTTPException(409, 'User confirmation of the current instructions is required before completing the step')
        progress.status = 'COMPLETED'; progress.completed_at = now()
    if progress and payload.action == 'status':
        if not payload.status: raise HTTPException(422, 'Choose a build state')
        progress.status = payload.status; progress.checks_confirmed = False; progress.confirmed_at = None; progress.completed_at = None
    db.flush()
    all_complete = bool(steps) and all((r := db.get(StepProgress, (st.id, u.id))) is not None and r.status == 'COMPLETED' for st in steps)
    overall = 'COMPLETED' if all_complete else progress.status if progress and progress.status not in ('COMPLETED', 'NOT_STARTED') else 'IN_PROGRESS' if s.status != 'NOT_STARTED' or payload.action == 'start' else 'NOT_STARTED'
    w = db.get(WorkbenchState, pid)
    values = {'revision': s.revision + 1, 'current_step_id': current_id, 'status': overall, 'workspace_revision': w.revision if w else 0, 'updated_at': now()}
    if payload.experience: values['experience'] = payload.experience
    if 'selected_component_id' in payload.model_fields_set: values['selected_component_id'] = payload.selected_component_id
    if payload.unresolved_issues is not None: values['unresolved_issues'] = payload.unresolved_issues
    changed = db.execute(update(BuildSession).where(BuildSession.project_id == pid, BuildSession.user_id == u.id, BuildSession.revision == payload.expected_revision).values(**values))
    if changed.rowcount != 1: db.rollback(); raise HTTPException(409, 'Build progress changed. Reload before saving.')
    db.refresh(s); checkpoint(db, pid, u, s, steps)
    audit(db, 'build.step.' + payload.action if payload.action in ('confirm', 'complete') else 'build.checkpoint.saved', u.id, pid)
    db.commit(); return get_build(pid, db, u)


def ai_context(db, pid, u, payload):
    """Only scoped records are passed to the provider. Media bytes are never included in text JSON."""
    session = db.get(BuildSession, (pid, u.id))
    step_id = payload.build_step_id or (session.current_step_id if payload.copilot and session else None)
    step = scoped(db, BuildStep, pid, step_id, 'Build step') if step_id else None
    equipment = scoped(db, Equipment, pid, payload.equipment_id, 'Equipment') if payload.equipment_id else None
    images = []
    for mid in payload.media_ids:
        media = scoped(db, BuildMedia, pid, mid, 'Photo')
        if media.step_id and media.step_id != step_id: raise HTTPException(422, 'Inspection photo belongs to a different build step')
        images.append(media.image)
    eq, photos, missing = inventory(db, pid)
    progress = db.get(StepProgress, (step_id, u.id)) if step_id else None
    return {'session': session_info(session), 'current_step': step_info(step) if step else None,
        'step_progress': progress_info(progress), 'equipment': [equipment_info(e, photos) for e in eq], 'missing_parts': missing,
        'selected_equipment_id': equipment.id if equipment else None, 'intent': payload.intent,
        'physical_verification': 'NOT_VERIFIED'}, images, step_id


def record_inspection_state(db, pid, u, step_id, expected_revision):
    # A slow provider response must not overwrite a newer user checkpoint.
    changed = db.execute(update(BuildSession).where(BuildSession.project_id == pid, BuildSession.user_id == u.id, BuildSession.current_step_id == step_id, BuildSession.revision == expected_revision).values(status='NEEDS_REVIEW', revision=BuildSession.revision + 1, updated_at=now()))
    if changed.rowcount == 1:
        progress = db.get(StepProgress, (step_id, u.id))
        if not progress: progress = StepProgress(step_id=step_id, user_id=u.id); db.add(progress)
        progress.status = 'NEEDS_REVIEW'; progress.checks_confirmed = False; progress.confirmed_at = None; progress.completed_at = None
        db.flush()
        session=db.get(BuildSession,(pid,u.id));db.refresh(session)
        checkpoint(db,pid,u,session,db.scalars(select(BuildStep).where(BuildStep.project_id==pid).order_by(BuildStep.ordinal)).all())
    audit(db, 'build.inspection.recorded', u.id, pid)


def invalidate_workspace(db,pid,old_data,new_data,actor_id):
    """Changed saved assembly references reopen prior user confirmations."""
    if not db.get(BuildPlan,pid): return
    old={p['id']:p for p in old_data.get('parts',[])}
    new={p['id']:p for p in new_data.get('parts',[])}
    fields=['name','kind','specification','source_id','parent_id','x','y','z','rx','ry','rz','quantity']
    changed={identifier for identifier,part in old.items() if identifier not in new or any(part.get(k)!=new[identifier].get(k) for k in fields)}
    steps=db.scalars(select(BuildStep).where(BuildStep.project_id==pid)).all()
    affected=[s.id for s in steps if any(i in changed for i in s.component_ids)]
    if not affected:return
    db.execute(update(StepProgress).where(StepProgress.step_id.in_(affected),StepProgress.status!='NOT_STARTED').values(status='NEEDS_REVIEW',checks_confirmed=False,confirmed_at=None,completed_at=None))
    db.execute(update(BuildSession).where(BuildSession.project_id==pid).values(status='NEEDS_REVIEW',revision=BuildSession.revision+1,updated_at=now()))
    audit(db,'build.reference.changed',actor_id,pid)
