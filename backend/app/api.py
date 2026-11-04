import io, os, json, secrets, hashlib
from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, Response, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session
from .db import get_db
from .models import User, Project, Membership, HardwareProfile, Consent, Conversation, AuditEvent, LoginThrottle, EngineeringPlan, Session as LoginSession, now, as_utc
from .planning import FAMILIES, catalog, draft_engineering_plan
from sqlalchemy.exc import IntegrityError
from .security import password_hash, password_valid, current_user, csrf_guard, auth_origin, issue, clear, valid_session

app = FastAPI(title='RoboLN v2 API', version='3.0.0', docs_url='/api/docs', openapi_url='/api/openapi.json')

@app.middleware('http')
async def sensitive_api_response_headers(request: Request, call_next):
    # Privacy-sensitive JSON must not be cached by browsers/shared intermediaries.
    # These headers protect the API; separate HTTPS/security policy is required for Next.js.
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
    return response

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
class Registration(Credentials):
    full_name: str = Field(min_length=1, max_length=100)
    @field_validator('full_name')
    @classmethod
    def valid_full_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Full name cannot be blank')
        return value.strip()
class ProfileEdit(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    @field_validator('full_name')
    @classmethod
    def valid_full_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Full name cannot be blank')
        return value.strip()
class ThemeEdit(BaseModel):
    theme: Literal['light','dark','system']
class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default='', max_length=2000)
    goal: str = Field(default='', max_length=1000)
    @field_validator('name')
    @classmethod
    def strip(cls,v):
        if len(v.strip()) < 2: raise ValueError('Project name must contain at least two visible characters')
        return v.strip()
class ProjectEdit(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    description: str = Field(default='',max_length=2000)
    goal: str = Field(default='',max_length=1000)
    @field_validator('name')
    @classmethod
    def valid_project_name(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError('Project name must have at least two visible characters')
        return value.strip()
class MembershipEdit(BaseModel):
    email: EmailStr
    role: Literal['editor','viewer']
class HardwareEdit(BaseModel):
    device_class: Literal['MCU','SBC','OTHER'] = 'OTHER'
    board_model: str = Field(default='',max_length=160)
    board_revision: str = Field(default='',max_length=100)
    pin_map: dict[str,str] = Field(default_factory=dict)
    sensor_inventory: list[dict] = Field(default_factory=list, max_length=100)
    @field_validator('sensor_inventory')
    @classmethod
    def bounded_sensor_inventory(cls, value: list[dict]) -> list[dict]:
        # This is an unverified user draft, not an approved electrical specification.
        # Limit nested strings/objects so a small draft field cannot store arbitrarily
        # large documents or consume excessive storage on repeated submissions.
        if len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) > 32_768:
            raise ValueError('Sensor inventory draft exceeds 32 KiB')
        return value
    @field_validator('pin_map')
    @classmethod
    def bounded_pin_map(cls, value: dict[str,str]) -> dict[str,str]:
        if len(value)>100 or any(len(key)>80 or len(pin)>160 for key,pin in value.items()):
            raise ValueError('Pin map exceeds allowed size')
        return value
class ConsentEdit(BaseModel):
    enabled: bool
class DraftEdit(BaseModel):
    draft: str = Field(max_length=8000)

class PlanningIntake(BaseModel):
    family: str = Field(min_length=1,max_length=48)
    goal: str = Field(min_length=5,max_length=1200)
    available_parts: str = Field(default='',max_length=1600)
    @field_validator('goal')
    @classmethod
    def nonempty_goal(cls,value):
        if len(value.strip())<5: raise ValueError('State an actionable goal')
        return value.strip()


@app.get('/api/health')
def health():
    from .meta_ai import configuration
    return {'service':'RoboLN','status':'available','version':'3.0.0','ai_provider':configuration()['status'],'telemetry':'AUTHENTICATED_INGESTION','physical_validation':'NOT_PERFORMED'}

def audit(db, action, user=None, project_id=None):
    db.add(AuditEvent(action=action,actor_id=user, project_id=project_id))

def user_info(u:User): return {'id':u.id,'email':u.email,'full_name':u.full_name,'theme':u.theme}

def project_info(p:Project, role):
    return {'id':p.id,'name':p.name,'description':p.description,'goal':p.goal,'role':role,'archived':p.archived,'context_version':p.context_version,'created_at':as_utc(p.created_at)}

def authorized(db:Session, pid:str, user:User, write:bool=False, owner:bool=False):
    membership=db.get(Membership,(pid,user.id))
    if not membership: raise HTTPException(404,'Project not found')
    project=db.get(Project,pid)
    if not project: raise HTTPException(404,'Project not found')
    if owner and membership.role!='owner': raise HTTPException(403,'Owner access required')
    if write and project.archived: raise HTTPException(409,'Restore archived project before editing')
    if write and membership.role not in ('owner','editor'): raise HTTPException(403,'Editor access required')
    return project, membership.role

@app.post('/api/auth/register',status_code=201,dependencies=[Depends(auth_origin)])
def register(payload:Registration, response:Response, db:Session=Depends(get_db)):
    email=str(payload.email).lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,'Email already registered')
    u=User(email=email,full_name=payload.full_name.strip(),password_hash=password_hash(payload.password))
    db.add(u);db.flush();audit(db,'user.register',u.id); db.commit()
    issue(db,response,u)
    return user_info(u)

@app.post('/api/auth/login',dependencies=[Depends(auth_origin)])
def login(payload:Credentials,response:Response,request:Request,db:Session=Depends(get_db)):
    email=str(payload.email).lower()
    client_host=request.client.host if request.client else 'unknown'
    throttle_key=hashlib.sha256((email+'|'+client_host).encode()).hexdigest()
    t=db.get(LoginThrottle,throttle_key)
    if t and t.blocked_until and t.blocked_until.replace(tzinfo=timezone.utc)>now():
        raise HTTPException(429,'Too many failed logins. Try again later.')
    u=db.scalar(select(User).where(User.email==email))
    if not u or not password_valid(u.password_hash,payload.password):
        if not t:t=LoginThrottle(key=throttle_key,failures=0);db.add(t)
        if t.last_failure and t.last_failure.replace(tzinfo=timezone.utc) < now()-timedelta(minutes=15):t.failures=0
        t.failures+=1;t.last_failure=now()
        if t.failures>=5:t.blocked_until=now()+timedelta(minutes=15)
        db.commit()
        raise HTTPException(401,'Invalid credentials')
    if t:db.delete(t);db.commit()
    issue(db,response,u)
    audit(db,'user.login',u.id);db.commit()
    return user_info(u)

@app.get('/api/auth/me')
def me(u:User=Depends(current_user)): return user_info(u)

@app.post('/api/auth/logout',dependencies=[Depends(csrf_guard)])
def logout(request:Request,response:Response,db:Session=Depends(get_db),u:User=Depends(current_user)):
    s=valid_session(request.cookies.get('roboln_session'),db)
    if s: s.revoked=True
    audit(db,'user.logout',u.id);db.commit();clear(response)
    return {'ok':True}

@app.patch('/api/profile',dependencies=[Depends(csrf_guard)])
def change_profile(payload:ProfileEdit, db:Session=Depends(get_db),u:User=Depends(current_user)):
    u.full_name=payload.full_name.strip();audit(db,'user.profile',u.id);db.commit();return user_info(u)

@app.patch('/api/preferences/theme',dependencies=[Depends(csrf_guard)])
def change_theme(payload:ThemeEdit, db:Session=Depends(get_db),u:User=Depends(current_user)):
    u.theme=payload.theme;audit(db,'user.theme',u.id);db.commit();return user_info(u)

@app.get('/api/consents')
def list_consents(db:Session=Depends(get_db),u:User=Depends(current_user)):
    return {c.kind:c.enabled for c in db.scalars(select(Consent).where(Consent.user_id==u.id))}

@app.put('/api/consents/{kind}', dependencies=[Depends(csrf_guard)])
def set_consent(kind:Literal['camera','microphone','cloud_ai','notifications'],payload:ConsentEdit,db:Session=Depends(get_db),u:User=Depends(current_user)):
    c=db.get(Consent,(u.id,kind))
    if not c: c=Consent(user_id=u.id,kind=kind);db.add(c)
    c.enabled=payload.enabled;c.updated_at=now();audit(db,'consent.'+kind,u.id);db.commit();return {'kind':kind,'enabled':c.enabled}

@app.get('/api/projects')
def list_projects(db:Session=Depends(get_db),u:User=Depends(current_user)):
    rows=db.execute(select(Project,Membership.role).join(Membership,Project.id==Membership.project_id).where(Membership.user_id==u.id).order_by(Project.created_at.desc())).all()
    return [project_info(p,role) for p,role in rows]

@app.post('/api/projects',status_code=201,dependencies=[Depends(csrf_guard)])
def create_project(payload:ProjectCreate, db:Session=Depends(get_db),u:User=Depends(current_user)):
    p=Project(name=payload.name,description=payload.description,goal=payload.goal,owner_id=u.id)
    db.add(p);db.flush();db.add(Membership(project_id=p.id,user_id=u.id,role='owner'))
    audit(db,'project.create',u.id,p.id);db.commit();return project_info(p,'owner')

@app.get('/api/projects/{pid}')
def get_project(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,role=authorized(db,pid,u);return project_info(p,role)

@app.patch('/api/projects/{pid}',dependencies=[Depends(csrf_guard)])
def edit_project(pid:str,payload:ProjectEdit,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,role=authorized(db,pid,u,write=True)
    p.name=payload.name.strip();p.description=payload.description;p.goal=payload.goal;p.context_version+=1
    audit(db,'project.edit',u.id,pid);db.commit();return project_info(p,role)

@app.post('/api/projects/{pid}/archive',dependencies=[Depends(csrf_guard)])
def archive_project(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,role=authorized(db,pid,u,owner=True);p.archived=not p.archived;audit(db,'project.restore' if not p.archived else 'project.archive',u.id,pid);db.commit();return project_info(p,role)

@app.delete('/api/projects/{pid}',dependencies=[Depends(csrf_guard)],status_code=204)
def delete_project(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,owner=True);db.delete(p);audit(db,'project.delete',u.id,pid);db.commit()

@app.get('/api/projects/{pid}/members')
def members(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    rows=db.execute(select(User,Membership.role).join(Membership,User.id==Membership.user_id).where(Membership.project_id==pid)).all()
    return [{'id':m.id,'email':m.email,'full_name':m.full_name,'role':role} for m,role in rows]

@app.put('/api/projects/{pid}/members',dependencies=[Depends(csrf_guard)])
def add_member(pid:str,payload:MembershipEdit,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u,write=True,owner=True)
    target=db.scalar(select(User).where(User.email==str(payload.email).lower()))
    if not target: raise HTTPException(404,'Invitee must first create a RoboLN account')
    existing=db.get(Membership,(pid,target.id))
    if existing and existing.role=='owner': raise HTTPException(403,'Cannot change owner')
    if existing: existing.role=payload.role
    else: db.add(Membership(project_id=pid,user_id=target.id,role=payload.role))
    audit(db,'project.member.set',u.id,pid);db.commit();return {'id':target.id,'role':payload.role}

@app.delete('/api/projects/{pid}/members/{member_id}',dependencies=[Depends(csrf_guard)])
def remove_member(pid:str,member_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u,write=True,owner=True)
    member=db.get(Membership,(pid,member_id))
    if not member: raise HTTPException(404,'Member not found')
    if member.role=='owner': raise HTTPException(403,'Cannot remove project owner')
    db.delete(member);audit(db,'project.member.remove',u.id,pid);db.commit();return {'ok':True}

@app.get('/api/projects/{pid}/hardware')
def get_hardware(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    hp=db.scalar(select(HardwareProfile).where(HardwareProfile.project_id==pid))
    return {'id':hp.id,'board_model':hp.board_model,'board_revision':hp.board_revision,'device_class':hp.device_class,'profile_review_state':hp.profile_review_state,'pin_map':hp.pin_map,'sensor_inventory':hp.sensor_inventory} if hp else None

@app.put('/api/projects/{pid}/hardware',dependencies=[Depends(csrf_guard)])
def save_hardware(pid:str,payload:HardwareEdit,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,write=True)
    hp=db.scalar(select(HardwareProfile).where(HardwareProfile.project_id==pid))
    if not hp:hp=HardwareProfile(project_id=pid);db.add(hp)
    hp.board_model=payload.board_model.strip();hp.board_revision=payload.board_revision.strip();hp.device_class=payload.device_class
    hp.pin_map=payload.pin_map;hp.sensor_inventory=payload.sensor_inventory;hp.profile_review_state='REVIEW_REQUIRED'
    p.context_version+=1;audit(db,'hardware.draft',u.id,pid);db.commit()
    return {'id':hp.id,'profile_review_state':hp.profile_review_state,'board_model':hp.board_model}

@app.get('/api/projects/{pid}/context')
def context(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u)
    hp=db.scalar(select(HardwareProfile).where(HardwareProfile.project_id==pid))
    return {'project_id':p.id,'owner_scope':p.owner_id,'name':p.name,'hardware_profile_id':hp.id if hp else None,'context_version':p.context_version,'source_revision_ids':[],'taskpack_id':None,'code_artifact_ids':[],'device_ids':[],'timestamp':now().isoformat()}

@app.get('/api/projects/{pid}/draft')
def get_draft(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    d=db.scalar(select(Conversation).where(Conversation.project_id==pid,Conversation.user_id==u.id))
    return {'draft':d.draft if d else ''}

@app.put('/api/projects/{pid}/draft',dependencies=[Depends(csrf_guard)])
def save_draft(pid:str,payload:DraftEdit,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u,write=True)
    d=db.scalar(select(Conversation).where(Conversation.project_id==pid,Conversation.user_id==u.id))
    if not d:d=Conversation(project_id=pid,user_id=u.id);db.add(d)
    d.draft=payload.draft;d.updated_at=now();db.commit();return {'draft':d.draft}

@app.get('/api/planning/families')
def planning_families(u:User=Depends(current_user)):
    return {'families':catalog(),'model_inference':'NOT_AVAILABLE'}

def plan_info(row:EngineeringPlan):
    return {'id':row.id,'project_id':row.project_id,'revision':row.revision,
            'context_version':row.context_version,'status':row.status,
            'created_at':as_utc(row.created_at),'document':row.document}

@app.get('/api/projects/{pid}/engineering-plans')
def engineering_plans(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    rows=db.scalars(select(EngineeringPlan).where(EngineeringPlan.project_id==pid).order_by(EngineeringPlan.revision.desc()).limit(100)).all()
    return {'plans':[plan_info(row) for row in rows]}

@app.post('/api/projects/{pid}/engineering-plans',status_code=201,dependencies=[Depends(csrf_guard)])
def create_engineering_plan(pid:str,payload:PlanningIntake,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,write=True)
    if payload.family not in FAMILIES:
        raise HTTPException(422,'Unsupported project family')
    hardware=db.scalar(select(HardwareProfile).where(HardwareProfile.project_id==pid))
    board=hardware.board_model if hardware else ''
    revision=hardware.board_revision if hardware else ''
    doc=draft_engineering_plan(family_key=payload.family, goal=payload.goal, board=board, revision=revision,
                               available_parts=payload.available_parts,context_version=p.context_version)
    latest=db.scalar(select(func.max(EngineeringPlan.revision)).where(EngineeringPlan.project_id==pid)) or 0
    if latest>=100:raise HTTPException(409,'Plan revision limit reached. Export records before creating another.')
    plan=EngineeringPlan(project_id=pid, author_id=u.id,revision=latest+1,
        context_version=p.context_version,family=payload.family,status='DRAFT',document=doc)
    db.add(plan);audit(db,'plan.draft.created',u.id,pid)
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Another plan revision was saved. Refresh and try again.')
    return plan_info(plan)

@app.get('/api/projects/{pid}/engineering-plans/{plan_id}')
def engineering_plan_detail(pid:str,plan_id:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    row=db.get(EngineeringPlan,plan_id)
    if row is None or row.project_id!=pid:raise HTTPException(404,'Plan not found')
    return plan_info(row)

@app.get('/api/projects/{pid}/evidence')
def get_evidence(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    # Only actual stored application audit events are displayed. None is proof of
    # physical assembly or hardware compliance. Keep actor data private.
    rows=db.scalars(select(AuditEvent).where(AuditEvent.project_id==pid).order_by(AuditEvent.at.desc()).limit(100)).all()
    labels={'project.create':'Project created','project.edit':'Project details updated','project.archive':'Project archived',
            'project.restore':'Project restored','hardware.draft':'Hardware draft saved — unverified',
            'plan.draft.created':'Engineering draft revision saved — unverified',
            'build.reference.changed':'Saved assembly changed — build confirmations need review','build.plan.created':'Guided build plan saved — review required','equipment.created':'Equipment added to project inventory','equipment.corrected':'Equipment identification corrected','equipment.deleted':'Equipment removed','build.photo.saved':'Build photo stored with consent','build.photo.deleted':'Build photo removed','build.checkpoint.saved':'Build progress checkpoint saved','build.step.confirm':'Build checks confirmed by user','build.step.complete':'Assembly step marked complete by user','build.step.edited':'Assembly instructions changed — review reopened','build.step.appended':'New assembly step saved','build.inspection.recorded':'AI snapshot feedback saved — not physical verification',
            'project.member.set':'Project member access changed','project.member.remove':'Project member removed'}
    events=[{'id':e.id,'description':labels.get(e.action,'Project event recorded'),
             'event_type':e.action,'at':as_utc(e.at),'evidence_kind':'ACCOUNT_ACTIVITY',
             'physical_verification':'NOT_ASSESSED'} for e in rows]
    from .workbench_models import Observation
    observed=db.scalar(select(func.count()).select_from(Observation).where(Observation.project_id==pid)) or 0
    return {'events':events,'state':'ACCOUNT_ACTIVITY_ONLY' if observed==0 else 'ACTIVITY_WITH_USER_OBSERVATIONS',
            'physical_observations':observed,'message':'Activity events are not hardware evidence. User-reported observations are available separately; they are not independent RoboLN certification.'}

@app.get('/api/projects/{pid}/twin')
def twin(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u)
    from .workbench import full_twin
    return full_twin(pid,db,u)

@app.get('/api/account/export')
def export_account(response:Response,db:Session=Depends(get_db),u:User=Depends(current_user)):
    """Export the user's accessible engineering work, without session secrets or other users' drafts."""
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Disposition']='attachment; filename="roboln-account-export.json"'
    rows=db.execute(select(Project,Membership.role).join(Membership,Project.id==Membership.project_id).where(Membership.user_id==u.id).order_by(Project.created_at.desc())).all()
    projects=[]
    for p,role in rows:
        hp=db.scalar(select(HardwareProfile).where(HardwareProfile.project_id==p.id))
        draft=db.scalar(select(Conversation).where(Conversation.project_id==p.id,Conversation.user_id==u.id))
        project=project_info(p,role)
        project['hardware_draft']={
            'device_class':hp.device_class,'board_model':hp.board_model,
            'board_revision':hp.board_revision,'profile_review_state':hp.profile_review_state,
            'pin_map':hp.pin_map,'sensor_inventory':hp.sensor_inventory,
            'source_revision_ids':hp.source_revision_ids
        } if hp else None
        project['my_draft']=draft.draft if draft else ''
        mine=db.scalars(select(EngineeringPlan).where(EngineeringPlan.project_id==p.id,EngineeringPlan.author_id==u.id).order_by(EngineeringPlan.revision)).all()
        project['my_engineering_plan_revisions']=[plan_info(plan) for plan in mine]
        from .copilot import get_build
        project['my_build_memory']=get_build(p.id,db,u)
        projects.append(project)
    cons={c.kind:c.enabled for c in db.scalars(select(Consent).where(Consent.user_id==u.id))}
    events=db.scalars(select(AuditEvent).where(AuditEvent.actor_id==u.id).order_by(AuditEvent.at)).all()
    return {
        'exported_at':now().isoformat(),'user':user_info(u),
        'projects':projects,'consents':cons,
        'my_audit_events':[{'action':e.action,'project_id':e.project_id,'at':as_utc(e.at)} for e in events],
        'limitations':['Contains only projects currently accessible to this account.',
                       'Project drafts belong to the exporting user; other members drafts are excluded.',
                       'Additional project sources, observations, workspace exports and telemetry are available through project APIs; this account export excludes binary media and device credentials.']
    }

@app.delete('/api/account',dependencies=[Depends(csrf_guard)])
def delete_account(response:Response,db:Session=Depends(get_db),u:User=Depends(current_user)):
    owned=db.scalars(select(Project).where(Project.owner_id==u.id)).all()
    for p in owned: db.delete(p)
    db.flush()
    db.delete(u);db.commit();clear(response)
    return {'deleted':True}

from .workbench import router as workbench_router
app.include_router(workbench_router)

from fastapi.exceptions import RequestValidationError
from .http_policy import validation_errors, RequestSizeLimit
app.add_exception_handler(RequestValidationError,validation_errors)
app.add_middleware(RequestSizeLimit)

@app.get('/api/ready')
def ready(db:Session=Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text('SELECT 1 FROM users LIMIT 1'))
        db.execute(text('SELECT 1 FROM build_sessions LIMIT 1'))
        return {'status':'ready','database':'available'}
    except Exception: raise HTTPException(503,'Database unavailable or migrations not applied')

from .industrial import router as industrial_router
app.include_router(industrial_router)
from .copilot import router as copilot_router
app.include_router(copilot_router)
from sqlalchemy.exc import OperationalError
from fastapi.responses import JSONResponse
import logging
@app.exception_handler(OperationalError)
async def database_unavailable(request:Request,exc:OperationalError):
    logging.getLogger('roboln').error('Database unavailable at %s; parameters withheld',request.url.path)
    return JSONResponse({'detail':'Database unavailable or busy. Inspect API storage and migrations.','code':'DATABASE_UNAVAILABLE'},status_code=503,headers={'Retry-After':'2'})
