"""Recovery release regression tests. Provider and physical-origin packets are explicit software fixtures."""
import json,math
from datetime import datetime,timedelta,timezone
import httpx,pytest
from tests.conftest import csrf
from tests.test_workbench import project,device,packet,ingest,consent,fake_provider
from app.simulation import simulate
from app.api import app
from app.db import get_db
from app.industrial_models import SensorReading
from sqlalchemy import select

def assembly(c,p):
    data={'expected_revision':0,'parts':[{'id':'chassis','name':'Generic chassis','kind':'chassis'},{'id':'soil','name':'Moisture sensor','kind':'sensor','parent_id':'chassis','ry':25},{'id':'wheel','name':'Measured wheel','kind':'wheel','parent_id':'chassis'}],'pins':[{'pin':'USER_PIN','signal':'Draft signal','component_id':'soil'}]}
    r=c.put(p+'/workbench',headers=csrf(c),json=data);assert r.status_code==200,r.text
    return r.json()
def mapping(c,p,d,**patch):
    data={'device_id':d['id'],'component_id':'soil','measurement':'soil_moisture','unit':'%','lower':20,'upper':80};data.update(patch)
    return c.post(p+'/twin/mappings',headers=csrf(c),json=data)
def test_layout_persistence_and_hierarchy_validation(client,register):
    register(client);p=project(client);w=assembly(client,p);assert w['data']['parts'][1]['ry']==25
    data=w['data'];data['parts'][0]['parent_id']='soil'
    assert client.put(p+'/workbench',headers=csrf(client),json={'expected_revision':1,**data}).status_code==422
    data['parts'][0]['parent_id']=None;data['pins'][0]['component_id']='outside'
    assert client.put(p+'/workbench',headers=csrf(client),json={'expected_revision':1,**data}).status_code==422
    assert client.get(p+'/workbench').json()['revision']==1
@pytest.mark.parametrize('patch',[{'device_id':'outside'},{'component_id':'outside'},{'channel':'WHEEL_ANGLE'},{'unit':' '},{'lower':90,'upper':20},{'stale_after':1}])
def test_mapping_rejects_invalid_scope_units_bounds(client,register,patch):
    register(client);p=project(client);assembly(client,p);d=device(client,p)
    assert mapping(client,p,d,**patch).status_code in (404,422)
def test_live_mapping_history_freshness_revocation_and_real_values(client,register):
    register(client);p=project(client);assembly(client,p);d=device(client,p,'LIVE_REAL');assert mapping(client,p,d).status_code==201
    assert ingest(client,d,packet(measurements=[{'name':'soil_moisture','value':12.5,'unit':'%'}])).status_code==201
    snap=client.get(p+'/twin/snapshot').json();s=snap['component_states'][0];assert s['value']==12.5 and s['live_eligible'] and s['review_band']=='LOW' and s['history'][0]['telemetry_id']==s['telemetry_id']
    generator=app.dependency_overrides[get_db]();db=next(generator)
    try:r=db.scalar(select(SensorReading));r.observed_at=datetime.now(timezone.utc)-timedelta(minutes=3);db.commit()
    finally:generator.close()
    snap=client.get(p+'/twin/snapshot').json();assert snap['devices'][0]['connection']=='LIVE_REAL';assert snap['component_states'][0]['status']=='STALE' and not snap['component_states'][0]['live_eligible']
    assert client.post(p+'/devices/'+d['id']+'/revoke',headers=csrf(client)).status_code==200
    assert client.get(p+'/twin/snapshot').json()['component_states'][0]['status']=='REVOKED'
def test_simulation_stream_excluded_and_mapping_isolation(client,register):
    register(client);p=project(client);assembly(client,p);d=device(client,p);m=mapping(client,p,d);assert m.status_code==201
    assert ingest(client,d).status_code==201
    s=client.get(p+'/twin/snapshot').json()['component_states'][0];assert s['origin']=='SIMULATION' and not s['live_eligible']
    other=project(client,'Other');assembly(client,other);assert mapping(client,other,d).status_code==404
    assert mapping(client,p,d).status_code==409
    assert client.delete(p+'/twin/mappings/'+m.json()['id'],headers=csrf(client)).status_code==204
    assert client.get(p+'/twin/snapshot').json()['component_states']==[]
def test_custom_units_and_orphaned_components(client,register):
    register(client);p=project(client);w=assembly(client,p);d=device(client,p,'LIVE_REAL');assert mapping(client,p,d,component_id='wheel',measurement='encoder_angle',unit='deg',channel='WHEEL_ANGLE').status_code==201
    assert ingest(client,d,packet(measurements=[{'name':'encoder_angle','value':90,'unit':'rad'}])).status_code==422
    assert ingest(client,d,packet(measurements=[{'name':'encoder_angle','value':90,'unit':'deg'}])).status_code==201
    w['data']['parts']=w['data']['parts'][:-1];assert client.put(p+'/workbench',headers=csrf(client),json={'expected_revision':1,**w['data']}).status_code==200
    s=client.get(p+'/twin/snapshot').json()['component_states'][0];assert s['status']=='ORPHANED_COMPONENT' and not s['live_eligible']
def test_deterministic_virtual_runs_separate_and_scoped(client,register):
    register(client);p=project(client);assembly(client,p);payload={'scenario':'sensor_dropout','duration':4}
    a=client.post(p+'/simulation/runs',headers=csrf(client),json=payload);b=client.post(p+'/simulation/runs',headers=csrf(client),json=payload);assert a.status_code==201 and b.status_code==201;assert a.json()['trace']==b.json()['trace'];assert a.json()['trace'][-1]['soil_moisture'] is None
    assert client.get(p+'/telemetry/history').json()==[]
    assert client.get(p+'/simulation/runs/'+a.json()['id']).json()['workspace_revision']==1
    other=project(client,'Other');assert client.get(other+'/simulation/runs/'+a.json()['id']).status_code==404
@pytest.mark.parametrize('turn',[0,60])
def test_kinematic_analytic_path(turn):
    trace,_=simulate({'duration':6,'scenario':'bench','speed':.35,'turn_rate':turn,'wheel_radius':.36,'moisture':45});last=trace[-1]
    assert abs(last['x'])<1e-5
    assert abs(last['z']-(2.1 if turn==0 else 0))<1e-5
    assert all(p['origin']=='SIMULATION' for p in trace)
def test_selected_context_and_explicit_reviewed_proposal(client,register,monkeypatch):
    register(client);p=project(client);assembly(client,p);consent(client);captured=[]
    def provider(req):
        captured.append(json.loads(req.content));return httpx.Response(200,json={'id':'mock-contract-only','model':'muse-spark-1.3','choices':[{'message':{'content':'REVIEW: obtain exact sensor voltage and controller logic evidence.'}}]})
    fake_provider(monkeypatch,provider)
    r=client.post(p+'/ai/ask',headers=csrf(client),json={'consent':True,'question':'Can I connect this sensor safely?','selected_component_id':'soil'});assert r.status_code==200,r.text
    assert 'selected_component' in json.dumps(captured) and 'Moisture sensor' in json.dumps(captured)
    proposal=client.post(p+'/ai/proposals',headers=csrf(client),json={'message_id':r.json()['id'],'component_id':'soil','specification':'Review exact logic voltage before connection','reason':'Missing manufacturer datasheet evidence'});assert proposal.status_code==201,proposal.text
    path=p+'/ai/proposals/'+proposal.json()['id']+'/review';assert client.post(path,headers=csrf(client),json={'decision':'APPROVE'}).status_code==422
    assert client.post(path,headers=csrf(client),json={'decision':'APPROVE','acknowledge':True}).status_code==200
    w=client.get(p+'/workbench').json();assert w['revision']==2 and w['data']['parts'][1]['specification'].startswith('Review exact')
    assert client.post(path,headers=csrf(client),json={'decision':'APPROVE','acknowledge':True}).status_code==409
def test_new_route_csrf_roles_and_isolation(client,register):
    register(client);p=project(client);assembly(client,p);d=device(client,p)
    assert client.post(p+'/twin/mappings',json={'device_id':d['id'],'component_id':'soil','measurement':'soil_moisture','unit':'%'}).status_code==403
    owner=dict(client.cookies);client.cookies.clear();register(client,'reader@example.com','Reader');reader=dict(client.cookies);client.cookies.clear();client.cookies.update(owner)
    assert client.put(p+'/members',headers=csrf(client),json={'email':'reader@example.com','role':'viewer'}).status_code==200
    client.cookies.clear();client.cookies.update(reader)
    assert client.get(p+'/twin/snapshot').status_code==200
    assert mapping(client,p,d).status_code==403
    assert client.post(p+'/simulation/runs',headers=csrf(client),json={}).status_code==403
    client.cookies.clear();register(client,'outsider@example.com','Outsider')
    assert client.get(p+'/twin/snapshot').status_code==404
    assert client.get(p+'/simulation/runs').status_code==404

def test_database_failure_is_structured_not_connection_reset(client,register,monkeypatch):
    register(client);p=project(client)
    from app import industrial
    from sqlalchemy.exc import OperationalError
    def broken(*args,**kwargs):raise OperationalError('query',{},Exception('private database detail'))
    monkeypatch.setattr(industrial,'authorized',broken)
    r=client.get(p+'/twin/snapshot');assert r.status_code==503 and r.json()['code']=='DATABASE_UNAVAILABLE';assert 'private database detail' not in r.text
