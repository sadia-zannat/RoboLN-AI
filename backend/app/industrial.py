"""Authenticated mappings, coherent snapshots, virtual runs and reviewed AI proposals."""
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field,model_validator
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .db import get_db
from .models import User,now,as_utc
from .security import current_user,csrf_guard
from .api import authorized,audit
from .workbench_models import Device,WorkbenchState,WorkbenchRevision,ChatMessage,Observation,ControlRequest
from .industrial_models import ComponentMapping,SensorReading,SimulationRun,ChangeProposal
from .workbench import aware,device_info,telemetry_history,control_info
from .simulation import simulate
router=APIRouter(prefix='/api/projects/{pid}');write=[Depends(csrf_guard)]
CHANNELS={'WHEEL_ANGLE':'deg','MOTOR_RPM':'rpm','POSE_X':'m','POSE_Z':'m','POSE_YAW':'deg','PUMP_STATE':'bool'}
def component(db,pid,cid):
    s=db.get(WorkbenchState,pid);c=next((c for c in (s.data.get('parts',[]) if s else []) if c['id']==cid),None)
    if not c:raise HTTPException(404,'Project component not found')
    return c,s
def band(m,v):return 'LOW' if m.lower is not None and v<m.lower else 'HIGH' if m.upper is not None and v>m.upper else 'IN_RANGE'
def validate_mapped_packet(db,d,measurements):
    maps={m.measurement:m for m in db.scalars(select(ComponentMapping).where(ComponentMapping.device_id==d.id))}
    for v in measurements:
        m=maps.get(v.name)
        if m and m.unit!=v.unit:raise HTTPException(422,f'Mapped stream {v.name} requires unit {m.unit}')
        if m and m.channel=='PUMP_STATE' and v.value not in (0,1):raise HTTPException(422,'PUMP_STATE requires 0 or 1')
def record_readings(db,d,t):
    maps={m.measurement:m for m in db.scalars(select(ComponentMapping).where(ComponentMapping.device_id==d.id))}
    for v in t.measurements:
        db.add(SensorReading(telemetry_id=t.id,device_id=d.id,name=v['name'],value=v['value'],unit=v['unit'],observed_at=t.observed_at,received_at=t.received_at))
        if v['name'] in maps and band(maps[v['name']],v['value'])!='IN_RANGE':audit(db,'twin.threshold.review',None,d.project_id)
class MappingCreate(BaseModel):
    device_id:str=Field(max_length=36)
    component_id:str=Field(max_length=60)
    measurement:str=Field(pattern=r'^[a-z][a-z0-9_]{0,59}$')
    unit:str=Field(min_length=1,max_length=24)
    channel:Literal['VALUE_ONLY','WHEEL_ANGLE','MOTOR_RPM','POSE_X','POSE_Z','POSE_YAW','PUMP_STATE']='VALUE_ONLY'
    stale_after:int=Field(default=60,ge=5,le=600)
    lower:float|None=Field(default=None,allow_inf_nan=False)
    upper:float|None=Field(default=None,allow_inf_nan=False)
    @model_validator(mode='after')
    def valid(self):
        if not self.unit.strip():raise ValueError('Unit is required')
        if self.lower is not None and self.upper is not None and self.lower>=self.upper:raise ValueError('Lower must be less than upper')
        if self.channel in CHANNELS and self.unit!=CHANNELS[self.channel]:raise ValueError('Wrong visual channel unit')
        return self
def mapping_info(m):return {k:getattr(m,k) for k in ['id','device_id','component_id','measurement','unit','channel','stale_after','lower','upper']}
@router.get('/twin/mappings')
def mappings(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u);return [mapping_info(m) for m in db.scalars(select(ComponentMapping).where(ComponentMapping.project_id==pid))]
@router.post('/twin/mappings',status_code=201,dependencies=write)
def create_mapping(pid:str,payload:MappingCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,write=True);component(db,pid,payload.component_id);d=db.get(Device,payload.device_id)
    if not d or d.project_id!=pid or d.revoked:raise HTTPException(404,'Active project device not found')
    if db.scalar(select(func.count()).select_from(ComponentMapping).where(ComponentMapping.project_id==pid))>=80:raise HTTPException(409,'Mapping limit reached')
    if payload.channel!='VALUE_ONLY' and db.scalar(select(ComponentMapping).where(ComponentMapping.project_id==pid,ComponentMapping.component_id==payload.component_id,ComponentMapping.channel==payload.channel)):raise HTTPException(409,'Visual channel already has a source')
    m=ComponentMapping(project_id=pid,**payload.model_dump());db.add(m);p.context_version+=1;audit(db,'twin.mapping.create',u.id,pid)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Device stream already mapped')
    return mapping_info(m)
@router.delete('/twin/mappings/{mid}',status_code=204,dependencies=write)
def remove_mapping(pid:str,mid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,write=True);m=db.get(ComponentMapping,mid)
    if not m or m.project_id!=pid:raise HTTPException(404,'Mapping not found')
    db.delete(m);p.context_version+=1;audit(db,'twin.mapping.delete',u.id,pid);db.commit()
@router.get('/twin/snapshot')
def snapshot(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u);devices=db.scalars(select(Device).where(Device.project_id==pid)).all();by_id={d.id:d for d in devices};ds=[device_info(db,d) for d in devices]
    ws=db.get(WorkbenchState,pid);ids={c['id'] for c in ws.data.get('parts',[])} if ws else set();states=[]
    for m in db.scalars(select(ComponentMapping).where(ComponentMapping.project_id==pid)):
        d=by_id[m.device_id];points=db.scalars(select(SensorReading).where(SensorReading.device_id==d.id,SensorReading.name==m.measurement).order_by(SensorReading.observed_at.desc()).limit(60)).all();r=points[0] if points else None
        status='ORPHANED_COMPONENT' if m.component_id not in ids else 'REVOKED' if d.revoked else 'ARCHIVED' if p.archived else 'NO_DATA' if r is None else 'UNIT_MISMATCH' if r.unit!=m.unit else 'STALE' if max((now()-aware(r.observed_at)).total_seconds(),(now()-aware(r.received_at)).total_seconds())>m.stale_after else 'FRESH'
        states.append({**mapping_info(m),'device_name':d.name,'origin':d.mode,'status':status,'live_eligible':status=='FRESH' and d.mode=='LIVE_REAL','value':r.value if r else None,'observed_at':as_utc(r.observed_at) if r else None,'received_at':as_utc(r.received_at) if r else None,'telemetry_id':r.telemetry_id if r else None,'review_band':band(m,r.value) if r else 'UNKNOWN','history':[{'value':v.value,'unit':v.unit,'observed_at':as_utc(v.observed_at),'telemetry_id':v.telemetry_id} for v in reversed(points)]})
    history=telemetry_history(pid,None,100,db,u);obs=db.scalars(select(Observation).where(Observation.project_id==pid).order_by(Observation.created_at.desc()).limit(20)).all()
    return {'project_id':pid,'server_time':now().isoformat(),'workspace_revision':ws.revision if ws else 0,'physical_connection':'LIVE_REAL' if any(d['connection']=='LIVE_REAL' for d in ds) else 'DISCONNECTED','connection':'NOT_ENROLLED' if not ds else 'LIVE_REAL' if any(d['connection']=='LIVE_REAL' for d in ds) else 'SIMULATION' if any(d['connection']=='SIMULATION' for d in ds) else 'OFFLINE','devices':ds,'component_states':states,'history':history,'controls':[control_info(c) for c in db.scalars(select(ControlRequest).where(ControlRequest.project_id==pid).order_by(ControlRequest.created_at.desc()).limit(100))],'events':[{'id':h['id'],'telemetry_id':h['id'],'message':h['event'],'origin':h['origin'],'at':h['observed_at']} for h in history if h['event']],'observations':[{'id':o.id,'component_id':o.component_id,'title':o.title,'state':o.state,'method':o.method,'at':as_utc(o.created_at)} for o in obs],'alerts':[{'component_id':s['component_id'],'mapping_id':s['id'],'state':s['status'] if s['status']!='FRESH' else s['review_band'],'origin':s['origin']} for s in states if s['status']!='FRESH' or s['review_band']!='IN_RANGE'],'control_dispatch':'HOLD_NO_EXECUTOR'}
class SimulationCreate(BaseModel):
    scenario:Literal['bench','dry_soil','obstacle_stop','sensor_dropout']='bench'
    duration:int=Field(default=20,ge=2,le=60)
    speed:float=Field(default=.35,ge=0,le=1,allow_inf_nan=False)
    turn_rate:float=Field(default=0,ge=-60,le=60,allow_inf_nan=False)
    wheel_radius:float=Field(default=.36,ge=.05,le=1,allow_inf_nan=False)
    moisture:float=Field(default=45,ge=0,le=100,allow_inf_nan=False)
def run_info(r,detail=True):
    data={'id':r.id,'workspace_revision':r.workspace_revision,'parameters':r.parameters,'events':r.events,'created_at':as_utc(r.created_at),'origin':'SIMULATION','model':'PLANAR_CONSTANT_TWIST_V1','physical_validation':'NOT_PERFORMED'}
    if detail:data['trace']=r.trace
    return data
@router.get('/simulation/runs')
def runs(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u);return [run_info(r,False) for r in db.scalars(select(SimulationRun).where(SimulationRun.project_id==pid).order_by(SimulationRun.created_at.desc()).limit(50))]
@router.post('/simulation/runs',status_code=201,dependencies=write)
def create_run(pid:str,payload:SimulationCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u,write=True);s=db.get(WorkbenchState,pid)
    if not s or not s.data.get('parts'):raise HTTPException(409,'Save components first')
    if db.scalar(select(func.count()).select_from(SimulationRun).where(SimulationRun.project_id==pid))>=100:raise HTTPException(409,'Virtual run limit reached')
    trace,events=simulate(payload.model_dump());r=SimulationRun(project_id=pid,author_id=u.id,workspace_revision=s.revision,parameters=payload.model_dump(),trace=trace,events=events);db.add(r);audit(db,'simulation.run',u.id,pid);db.commit();return run_info(r)
@router.get('/simulation/runs/{rid}')
def read_run(pid:str,rid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u);r=db.get(SimulationRun,rid)
    if not r or r.project_id!=pid:raise HTTPException(404,'Virtual run not found')
    return run_info(r)
class ProposalCreate(BaseModel):
    message_id:str=Field(max_length=36)
    component_id:str=Field(max_length=60)
    specification:str=Field(min_length=5,max_length=1000)
    reason:str=Field(min_length=5,max_length=1000)
class ProposalReview(BaseModel):
    decision:Literal['APPROVE','REJECT']
    acknowledge:bool=False
def proposal_info(r):return {**{k:getattr(r,k) for k in ['id','message_id','component_id','workspace_revision','original','proposed','reason','state']},'physical_actuation':'HOLD'}
@router.get('/ai/proposals')
def proposals(pid:str,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u);return [proposal_info(r) for r in db.scalars(select(ChangeProposal).where(ChangeProposal.project_id==pid,ChangeProposal.author_id==u.id).order_by(ChangeProposal.created_at.desc()).limit(50))]
@router.post('/ai/proposals',status_code=201,dependencies=write)
def propose(pid:str,payload:ProposalCreate,db:Session=Depends(get_db),u:User=Depends(current_user)):
    authorized(db,pid,u,write=True);part,s=component(db,pid,payload.component_id);message=db.get(ChatMessage,payload.message_id)
    if not message or message.project_id!=pid or message.user_id!=u.id or message.selected_component_id!=part['id']:raise HTTPException(404,'Genuine selected-component response required')
    r=ChangeProposal(project_id=pid,author_id=u.id,message_id=message.id,component_id=part['id'],workspace_revision=s.revision,original=part.get('specification',''),proposed=payload.specification,reason=payload.reason);db.add(r);audit(db,'ai.proposal.create',u.id,pid);db.commit();return proposal_info(r)
@router.post('/ai/proposals/{rid}/review',dependencies=write)
def review(pid:str,rid:str,payload:ProposalReview,db:Session=Depends(get_db),u:User=Depends(current_user)):
    p,_=authorized(db,pid,u,write=True);r=db.get(ChangeProposal,rid)
    if not r or r.project_id!=pid or r.author_id!=u.id:raise HTTPException(404,'Proposal not found')
    if r.state!='PENDING_REVIEW':raise HTTPException(409,'Already reviewed')
    if not payload.acknowledge:raise HTTPException(422,'Explicit review required')
    part,s=component(db,pid,r.component_id)
    if payload.decision=='APPROVE':
        if s.revision!=r.workspace_revision or part.get('specification','')!=r.original:raise HTTPException(409,'Revision changed; recreate proposal')
        s.data={**s.data,'parts':[{**c,'specification':r.proposed} if c['id']==part['id'] else c for c in s.data['parts']]};s.revision+=1;s.updated_at=now();p.context_version+=1;db.add(WorkbenchRevision(project_id=pid,revision=s.revision,author_id=u.id,data=s.data));r.state='APPROVED'
    else:r.state='REJECTED'
    audit(db,'ai.proposal.'+r.state.lower(),u.id,pid)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Concurrent edit; refresh')
    return proposal_info(r)
