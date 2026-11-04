"""Release tests run against isolated real SQL databases; provider traffic is explicitly mocked."""
import base64,io,json
from datetime import datetime,timedelta,timezone
import httpx,pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from tests.conftest import csrf
from app import meta_ai

def project(c,name='Workbench rover'):
    r=c.post('/api/projects',headers=csrf(c),json={'name':name,'goal':'Measure moisture safely'})
    assert r.status_code==201,r.text
    return '/api/projects/'+r.json()['id']

def photo():
    o=io.BytesIO();Image.new('RGB',(20,10),'blue').save(o,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(o.getvalue()).decode()

def source(c,p,name='sensor.txt',text=b'Sensor reference: signal is labeled SIG. Do not connect power without independent review.'):
    r=c.post(p+'/sources',files={'file':(name,text)},headers=csrf(c));assert r.status_code==201,r.text
    return r.json()

def device(c,p,mode='SIMULATION'):
    r=c.post(p+'/devices',headers=csrf(c),json={'name':'Lab controller','adapter':'ESP32','mode':mode})
    assert r.status_code==201,r.text
    return r.json()

def packet(**overrides):
    x={'packet_id':'p1','observed_at':datetime.now(timezone.utc).isoformat(),'measurements':[{'name':'soil_moisture','value':32.5,'unit':'%'}]};x.update(overrides);return x

def ingest(c,d,payload=None):return c.post('/api/device/telemetry',headers={'Authorization':'Bearer '+d['device_token']},json=payload or packet())

def consent(c):assert c.put('/api/consents/cloud_ai',headers=csrf(c),json={'enabled':True}).status_code==200

def fake_provider(monkeypatch,handler):
    real=httpx.Client
    monkeypatch.setattr(meta_ai.httpx,'Client',lambda **kwargs:real(**kwargs,transport=httpx.MockTransport(handler)))
    monkeypatch.setenv('MODEL_API_KEY','unit-test-provider-secret')

@pytest.mark.parametrize('suffix',['txt','md','csv','json'])
def test_source_roundtrip_retrieval_version_and_hash(client,register,suffix):
    register(client);p=project(client);s=source(client,p,'sensor.'+suffix)
    assert len(s['sha256'])==64
    s2=source(client,p,'sensor.'+suffix,b'New sensor revision. Signal SIG changed for user draft.')
    assert s2['version']==2 and s2['sha256']!=s['sha256']
    found=client.get(p+'/sources/search?q=signal').json()['results']
    assert found and all(x['source_id'] in (s['id'],s2['id']) for x in found)
    assert all(x['page'] is None for x in found)
    assert client.get(p+'/sources/'+s['id']+'/download').content.startswith(b'Sensor')
    assert client.get(p+'/sources/'+s['id']).json()['excerpts'][0]['index']==1

@pytest.mark.parametrize('name,data,code',[('source.exe',b'not executable',415),('bad.txt',b'\xff\x00',422),('bad.pdf',b'NOT PDF',422),('empty.md',b'',413),('large.txt',b'x'*(4*1024*1024+1),413)])
def test_sources_reject_unsupported_corrupt_empty_oversize(client,register,name,data,code):
    register(client);p=project(client)
    assert client.post(p+'/sources',headers=csrf(client),files={'file':(name,data)}).status_code==code
    assert client.get(p+'/sources').json()==[]

def pdf_bytes(texts):
    writer=PdfWriter()
    for text in texts:
        page=writer.add_blank_page(400,400)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject();stream.set_data(f'BT /F1 12 Tf 20 300 Td ({text}) Tj ET'.encode())
        page[NameObject('/Contents')]=writer._add_object(stream)
    out=io.BytesIO();writer.write(out);return out.getvalue()

def test_pdf_citations_use_genuine_extracted_page(client,register):
    register(client);p=project(client);s=source(client,p,'reference.pdf',pdf_bytes(['Board reference','Moisture calibration evidence']))
    found=client.get(p+'/sources/search?q=calibration').json()['results']
    assert len(found)==1 and found[0]['page']==2 and found[0]['source_id']==s['id']
    assert 'calibration evidence' in found[0]['text']

def test_source_and_observation_isolation_and_delete(client,register):
    register(client);p=project(client);s=source(client,p)
    obs=client.post(p+'/observations',headers=csrf(client),json={'title':'Unpowered build','image_data_url':photo(),'storage_consent':True}).json()
    other=project(client,'Other project')
    for endpoint in ['/sources/'+s['id'],'/sources/'+s['id']+'/download','/observations/'+obs['id']+'/image']:
        assert client.get(other+endpoint).status_code==404
    register(client,'outsider@example.com')
    for endpoint in ['/sources','/sources/search?q=signal','/observations','/workbench','/telemetry/twin','/ai/messages','/controls']:
        assert client.get(p+endpoint).status_code==404
    assert client.get(p+'/observations/'+obs['id']+'/image').status_code==404

@pytest.mark.parametrize('state',['UNKNOWN','REVIEW','FAIL','HOLD','PASS'])
def test_observation_states_require_independent_pass(client,register,state):
    register(client);p=project(client)
    data={'title':'Independent observation','state':state,'notes':'Meter continuity check completed with disconnected supply.','independent_check_confirmed':True}
    r=client.post(p+'/observations',headers=csrf(client),json=data);assert r.status_code==201,r.text
    assert r.json()['state']==state
    if state=='PASS':assert r.json()['method']=='USER_ATTESTED_INDEPENDENT_CHECK'
    assert len(client.get(p+'/observations').json())==1

def test_image_consent_validation_exif_and_deletion(client,register):
    register(client);p=project(client);data={'title':'Photo evidence','image_data_url':photo()}
    assert client.post(p+'/observations',headers=csrf(client),json=data).status_code==403
    data['storage_consent']=True;r=client.post(p+'/observations',headers=csrf(client),json=data);assert r.status_code==201,r.text
    oid=r.json()['id'];raw=client.get(p+'/observations/'+oid+'/image');assert raw.status_code==200
    im=Image.open(io.BytesIO(raw.content));assert im.format=='JPEG' and not im.getexif()
    assert client.post(p+'/observations',headers=csrf(client),json={'title':'Unverified PASS','state':'PASS','notes':'AI sees wires'}).status_code==422
    assert client.post(p+'/observations',headers=csrf(client),json={**data,'image_data_url':'data:image/png;base64,not-a-valid-image'}).status_code==422
    assert client.delete(p+'/observations/'+oid,headers=csrf(client)).status_code==204
    assert client.get(p+'/observations/'+oid+'/image').status_code==404

def test_workspace_revision_conflict_validation_and_export(client,register):
    register(client);p=project(client);assert client.get(p+'/workbench').json()['revision']==0
    data={'expected_revision':0,'requirements':'Read calibrated sensors','parts':[{'id':'board','name':'Controller','kind':'board'}],
        'pins':[{'pin':'GPIO2','signal':'sensor A'},{'pin':'gpio2','signal':'sensor B'}],'tasks':[{'id':'t1','title':'Independent voltage test'}]}
    r=client.put(p+'/workbench',headers=csrf(client),json=data);assert r.status_code==200,r.text
    assert r.json()['revision']==1
    assert client.put(p+'/workbench',headers=csrf(client),json=data).status_code==409
    checks=client.get(p+'/workbench/checks').json();assert checks['conflicts'] and checks['state']=='REVIEW'
    assert client.get(p+'/workbench/history').json()[0]['revision']==1
    assert client.get(p+'/engineering-export').json()['workspace']['data']['parts'][0]['name']=='Controller'
    data['expected_revision']=1;data['connections']=[{'start':'board','end':'nonexistent'}]
    assert client.put(p+'/workbench',headers=csrf(client),json=data).status_code==422
    data['connections']=[];data['parts'][0]['source_id']='foreign-source'
    assert client.put(p+'/workbench',headers=csrf(client),json=data).status_code==404

def test_ai_not_configured_and_consent_boundaries(client,register,monkeypatch):
    monkeypatch.delenv('MODEL_API_KEY',raising=False);register(client);p=project(client)
    assert client.get('/api/ai/status').json()['status']=='NOT_CONFIGURED'
    assert client.post(p+'/ai/ask',headers=csrf(client),json={'question':'What board evidence is missing?','consent':True}).status_code==403
    consent(client)
    assert client.post(p+'/ai/ask',headers=csrf(client),json={'question':'What board evidence is missing?','consent':True}).status_code==503
    assert client.get(p+'/ai/messages').json()==[]

def test_ai_actual_wire_contract_context_image_citations_history(client,register,monkeypatch):
    register(client);p=project(client);s=source(client,p);consent(client);captured=[]
    def handler(req):
        captured.append(json.loads(req.content));assert str(req.url)=='https://api.meta.ai/v1/chat/completions'
        assert req.headers['authorization']=='Bearer unit-test-provider-secret'
        return httpx.Response(200,json={'id':'mock-provider-123','model':'muse-spark-1.3','choices':[{'message':{'content':f'Check the SIG label [S:{s["id"]}:C:1]. Reject [S:invented:C:99].'},'finish_reason':'stop'}]})
    fake_provider(monkeypatch,handler)
    ask={'question':'Which signal label is documented?','consent':True,'image_data_url':photo(),'image_consent':True}
    r=client.post(p+'/ai/ask',headers=csrf(client),json=ask);assert r.status_code==200,r.text
    assert r.json()['provenance']=='PROVIDER_RESPONSE' and r.json()['verification']=='REVIEW'
    assert '[unverified source reference]' in r.json()['answer']
    assert captured[0]['model']=='muse-spark-1.3' and captured[0]['max_completion_tokens']==4000
    assert captured[0]['messages'][0]['role']=='developer'
    content=captured[0]['messages'][-1]['content'];assert content[1]['type']=='image_url' and 'data:image/jpeg' in content[1]['image_url']['url']
    assert 'Workbench rover' in content[0]['text'] and s['id'] in content[0]['text']
    assert client.get(p+'/ai/messages').json()[0]['provider_id']=='mock-provider-123'
    assert 'unit-test-provider-secret' not in client.get('/api/account/export').text

@pytest.mark.parametrize('status,expected',[(401,502),(403,502),(400,502),(429,429),(503,502)])
def test_ai_failures_never_persist_fake_answers(client,register,monkeypatch,status,expected):
    register(client);p=project(client);consent(client)
    fake_provider(monkeypatch,lambda req:httpx.Response(status,json={'error':'sensitive provider detail unit-test-provider-secret'}))
    r=client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Check missing engineering facts','consent':True})
    assert r.status_code==expected and 'unit-test-provider-secret' not in r.text
    assert client.get(p+'/ai/messages').json()==[]

def test_ai_timeout_invalid_response_and_revoke_consent(client,register,monkeypatch):
    register(client);p=project(client);consent(client)
    def timeout(req):raise httpx.ReadTimeout('private',request=req)
    fake_provider(monkeypatch,timeout)
    assert client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Board checks?','consent':True}).status_code==504
    monkeypatch.setattr(meta_ai,'provider_request',lambda *args,**kwargs:{'choices':[]})
    assert client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Board checks?','consent':True}).status_code==502
    client.put('/api/consents/cloud_ai',headers=csrf(client),json={'enabled':False})
    assert client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Board checks?','consent':True}).status_code==403

@pytest.mark.parametrize('mode',['LIVE_REAL','SIMULATION'])
def test_authenticated_ingestion_origin_history_and_revocation(client,register,mode):
    register(client);p=project(client);d=device(client,p,mode)
    assert client.get(p+'/telemetry/twin').json()['devices'][0]['connection']=='NO_DATA'
    r=ingest(client,d);assert r.status_code==201,r.text
    twin=client.get(p+'/twin').json();assert twin['connection']==mode
    assert twin['devices'][0]['latest']['measurements'][0]['value']==32.5
    history=client.get(p+'/telemetry/history').json();assert len(history)==1 and history[0]['origin']==mode
    assert 'device_token' not in client.get(p+'/devices').text
    assert ingest(client,d).status_code==409
    assert client.post(p+'/devices/'+d['id']+'/revoke',headers=csrf(client)).status_code==200
    assert ingest(client,d,packet(packet_id='p2')).status_code==401

@pytest.mark.parametrize('change',[
 {'measurements':[{'name':'soil_moisture','value':101,'unit':'%'}]},
 {'measurements':[{'name':'soil_moisture','value':20,'unit':'V'}]},
 {'observed_at':'2026-01-01T00:00:00'},
 {'observed_at':(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()},
 {'measurements':[]},
 {'measurements':[{'name':'pump_state','value':0.5,'unit':'bool'}]},
])
def test_telemetry_rejects_invalid_units_timestamps_and_values(client,register,change):
    register(client);p=project(client);d=device(client,p)
    assert ingest(client,d,packet(**change)).status_code==422
    assert client.get(p+'/telemetry/history').json()==[]

def test_stale_data_and_no_device_authorization_bypass(client,register):
    register(client);p=project(client);d=device(client,p)
    assert client.post('/api/device/telemetry',json=packet()).status_code==401
    assert client.post('/api/device/telemetry',json=packet(),headers={'Authorization':'Bearer wrong'}).status_code==401
    assert ingest(client,d,packet(observed_at=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat())).status_code==201
    assert client.get(p+'/telemetry/twin').json()['devices'][0]['connection']=='STALE'
    client.post(p+'/archive',headers=csrf(client))
    assert ingest(client,d,packet(packet_id='p2')).status_code==409


def test_viewer_denied_every_new_mutation(client,register):
    owner=register(client);p=project(client)
    viewer=register(client,'viewer-new@example.com')
    client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'})
    client.put(p+'/members',headers=csrf(client),json={'email':viewer['email'],'role':'viewer'})
    d=device(client,p);s=source(client,p)
    client.post('/api/auth/login',json={'email':viewer['email'],'password':'SafePasswordExample123!'})
    for suffix,data in [('/workbench',{'expected_revision':0}),('/observations',{'title':'Attempted write'}),('/devices',{'name':'Bad device','adapter':'ESP32','mode':'SIMULATION'}),('/ai/ask',{'question':'Can I mutate?','consent':True}),('/controls',{'device_id':d['id'],'action':'SAFE_STOP','reason':'Attempting owner review'})]:
        method=client.put if suffix=='/workbench' else client.post
        assert method(p+suffix,headers=csrf(client),json=data).status_code==403
    assert client.delete(p+'/sources/'+s['id'],headers=csrf(client)).status_code==403
    assert client.post(p+'/sources',files={'file':('x.txt',b'Private test')},headers=csrf(client)).status_code==403
    assert client.post(p+'/devices/'+d['id']+'/revoke',headers=csrf(client)).status_code==403
    assert client.get(p+'/ai/messages').json()==[]


def test_control_review_bound_to_context_no_execution(client,register):
    register(client);p=project(client);d=device(client,p)
    data={'device_id':d['id'],'action':'IRRIGATION_TEST','reason':'Supervised unpowered review only'}
    r=client.post(p+'/controls',headers=csrf(client),json=data);assert r.status_code==201,r.text
    cid=r.json()['id']
    review=p+'/controls/'+cid+'/review'
    assert client.post(review,headers=csrf(client),json={'decision':'APPROVE'}).status_code==422
    r=client.post(review,headers=csrf(client),json={'decision':'APPROVE','acknowledge':True})
    assert r.json()['state']=='APPROVED_HOLD' and r.json()['dispatch']=='HOLD_NO_EXECUTOR'
    assert client.post(review,headers=csrf(client),json={'decision':'APPROVE','acknowledge':True}).status_code==409
    r=client.post(p+'/controls',headers=csrf(client),json=data);cid=r.json()['id']
    client.put(p+'/hardware',headers=csrf(client),json={'board_model':'Changed board'})
    assert client.post(p+'/controls/'+cid+'/review',headers=csrf(client),json={'decision':'APPROVE','acknowledge':True}).status_code==409


def test_csrf_required_and_validation_redacted(client,register):
    register(client);p=project(client)
    for suffix,data in [('/workbench',{'expected_revision':0}),('/observations',{'title':'Test observation'}),('/ai/ask',{'question':'Question'})]:
        method=client.put if suffix=='/workbench' else client.post
        assert method(p+suffix,json=data).status_code==403
    r=client.post('/api/auth/login',json={'email':'invalid','password':'secret-short'})
    assert r.status_code==422 and 'secret-short' not in r.text
    r=client.post(p+'/observations',headers=csrf(client),content=b'x'*6_000_001)
    assert r.status_code==413


def test_persisted_history_timestamps_have_explicit_utc_offset(client,register):
    register(client);p=project(client);s=source(client,p)
    client.post(p+'/observations',headers=csrf(client),json={'title':'Timestamp observation'})
    records=[client.get(p).json()['created_at'],client.get(p+'/sources').json()[0]['created_at'],client.get(p+'/observations').json()[0]['created_at'],client.get(p+'/evidence').json()['events'][0]['at']]
    assert all(value.endswith('+00:00') for value in records),records
