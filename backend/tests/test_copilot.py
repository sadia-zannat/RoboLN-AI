"""Real database tests. Provider responses are explicitly mocked, never live claims."""
import io,json
import pytest,httpx
from PIL import Image
from tests.conftest import csrf
from tests.test_workbench import fake_provider,consent

def setup(c,register):
 register(c)
 r=c.post('/api/projects',headers=csrf(c),json={'name':'Guided rover','goal':'Supervised inspection rover'});assert r.status_code==201
 p='/api/projects/'+r.json()['id']
 r=c.put(p+'/workbench',headers=csrf(c),json={'expected_revision':0,'parts':[{'id':'frame','name':'Frame','kind':'chassis','y':1},{'id':'camera','name':'Camera','kind':'camera','parent_id':'frame','y':2}]});assert r.status_code==200,r.text
 return p

def plan(c,p,steps=None):
 r=c.post(p+'/build/plan',headers=csrf(c),json={'steps':steps} if steps else {});assert r.status_code==201,r.text
 return r.json()

def session(c,p,action='save',code=200,**extra):
 b=c.get(p+'/build').json();r=c.put(p+'/build/session',headers=csrf(c),json={'expected_revision':b['session']['revision'],'action':action,**extra});assert r.status_code==code,r.text
 return r.json()

def equipment(c,p):
 r=c.post(p+'/equipment',headers=csrf(c),json={'name':'Camera from label','category':'camera','bom_component_id':'camera','unknown_specs':'Electrical ratings unverified'});assert r.status_code==201,r.text
 return r.json()

def photo(c,p,**fields):
 o=io.BytesIO();Image.new('RGB',(16,12),'blue').save(o,format='PNG')
 return c.post(p+'/build/media',headers=csrf(c),data={'storage_consent':'true',**fields},files={'file':('unpowered.png',o.getvalue(),'image/png')})

def test_full_journey_inventory_photos_confirm_checkpoint_and_login(client,register):
 p=setup(client,register);e=equipment(client,p)
 for _ in range(2):assert photo(client,p,equipment_id=e['id']).status_code==201
 b=plan(client,p);assert len(b['steps'])==5 and len(b['equipment'][0]['photos'])==2
 assert [m['component_id'] for m in b['missing_parts']]==['frame']
 b=session(client,p,'start');first,second=b['steps'][:2]
 session(client,p,'complete',code=409)
 session(client,p,'confirm',code=422,notes='No test')
 session(client,p,'confirm',attestation=True,checks_confirmed=True,notes='Independent unpowered label check completed.')
 assert session(client,p,'complete')['completed_steps']==1
 session(client,p,'go',step_id=second['id'])
 session(client,p,notes='Waiting for exact datasheet.',experience='advanced',selected_component_id='camera',unresolved_issues=['Camera supply rating unknown'])
 client.post('/api/auth/logout',headers=csrf(client));assert client.get(p+'/build').status_code==401
 assert client.post('/api/auth/login',json={'email':'owner@example.com','password':'SafePasswordExample123!'}).status_code==200
 b=client.get(p+'/build').json();assert b['session']['current_step_id']==second['id'] and b['session']['experience']=='advanced'
 assert b['session']['selected_component_id']=='camera' and b['session']['unresolved_issues']==['Camera supply rating unknown']
 assert b['steps'][1]['progress']['notes']=='Waiting for exact datasheet.' and b['completed_steps']==1
 assert b['checkpoints'][0]['snapshot']['step_progress'][first['id']]['status']=='COMPLETED'
 assert b['physical_verification']=='NOT_VERIFIED'

@pytest.mark.parametrize('status',['WAITING_FOR_EVIDENCE','NEEDS_MORE_EVIDENCE','NEEDS_REVIEW','BLOCKED','IN_PROGRESS'])
def test_build_states_persist(client,register,status):
 p=setup(client,register);plan(client,p);session(client,p,'start')
 b=session(client,p,'status',status=status);assert b['session']['status']==status and b['steps'][0]['progress']['status']==status
 assert client.get(p+'/build').json()['session']['status']==status

def test_complete_requires_user_check_and_edited_step_reopens_review(client,register):
 p=setup(client,register);b=plan(client,p,[{'objective':'Check labels','instruction':'Compare unpowered labels to a source','evidence_required':True}]);sid=b['steps'][0]['id'];session(client,p,'start')
 session(client,p,'confirm',code=409,attestation=True,checks_confirmed=True,notes='Label checked')
 session(client,p,'confirm',attestation=True,checks_confirmed=True,notes='Label checked against independent source while disconnected.')
 assert session(client,p,'complete')['session']['status']=='COMPLETED'
 mid=photo(client,p,step_id=sid).json()['id']
 r=client.put(p+'/build/steps/'+sid,headers=csrf(client),json={'expected_plan_revision':1,'objective':'Check exact revision','instruction':'Read the printed revision with power disconnected.'});assert r.status_code==200,r.text
 assert r.json()['completed_steps']==0 and r.json()['session']['status']=='NEEDS_REVIEW'
 assert client.get(p+'/build/media/'+mid).status_code==200

def test_stale_progress_and_equipment_writes_rejected(client,register):
 p=setup(client,register);e=equipment(client,p);plan(client,p);b=session(client,p,'start');stale=b['session']['revision'];session(client,p,notes='New saved note')
 assert client.put(p+'/build/session',headers=csrf(client),json={'expected_revision':stale,'notes':'Stale overwrite'}).status_code==409
 assert client.get(p+'/build').json()['steps'][0]['progress']['notes']=='New saved note'
 assert client.put(p+'/equipment/'+e['id'],headers=csrf(client),json={'expected_revision':1,'name':'Corrected camera'}).status_code==200
 assert client.put(p+'/equipment/'+e['id'],headers=csrf(client),json={'expected_revision':1,'name':'Stale camera'}).status_code==409

def test_project_scope_and_private_member_progress(client,register):
 p=setup(client,register);e=equipment(client,p);b=plan(client,p);session(client,p,'start',notes='Private owner note');mid=photo(client,p,equipment_id=e['id']).json()['id']
 other='/api/projects/'+client.post('/api/projects',headers=csrf(client),json={'name':'Second private project'}).json()['id']
 assert client.get(other+'/build/media/'+mid).status_code==404
 assert photo(client,other,equipment_id=e['id']).status_code==404 and photo(client,other,step_id=b['steps'][0]['id']).status_code==404
 assert client.post(other+'/equipment',headers=csrf(client),json={'name':'Invalid scope','bom_component_id':'camera'}).status_code==422
 owner=dict(client.cookies);register(client,'build-editor@example.com');editor=dict(client.cookies);client.cookies.clear();client.cookies.update(owner)
 client.put(p+'/members',headers=csrf(client),json={'email':'build-editor@example.com','role':'editor'});client.cookies.clear();client.cookies.update(editor)
 b=client.get(p+'/build').json();assert b['session']['status']=='NOT_STARTED' and not b['checkpoints'] and b['steps'][0]['progress']['notes']==''
 assert b['equipment'][0]['id']==e['id'] and client.get(other+'/build').status_code==404

def test_viewer_archived_and_csrf_guards(client,register):
 p=setup(client,register);e=equipment(client,p);b=plan(client,p);owner=dict(client.cookies);register(client,'build-viewer@example.com');viewer=dict(client.cookies)
 client.cookies.clear();client.cookies.update(owner);client.put(p+'/members',headers=csrf(client),json={'email':'build-viewer@example.com','role':'viewer'});client.cookies.clear();client.cookies.update(viewer)
 assert client.get(p+'/build').status_code==200
 for method,url,body in [('post','/equipment',{'name':'Denied'}),('put','/equipment/'+e['id'],{'name':'Denied'}),('post','/build/plan',{}),('put','/build/session',{'expected_revision':0,'action':'start'}),('put','/build/steps/'+b['steps'][0]['id'],{'expected_plan_revision':1,'objective':'Denied','instruction':'Denied instructions'})]:
  assert getattr(client,method)(p+url,headers=csrf(client),json=body).status_code==403
 assert photo(client,p,equipment_id=e['id']).status_code==403
 client.cookies.clear();client.cookies.update(owner)
 assert client.put(p+'/build/session',json={'expected_revision':0}).status_code==403
 client.post(p+'/archive',headers=csrf(client));assert client.put(p+'/build/session',headers=csrf(client),json={'expected_revision':0,'action':'start'}).status_code==409

@pytest.mark.parametrize('mode,code',[('no_consent',403),('invalid_image',422),('wrong_type',415),('oversize',413)])
def test_photo_validation(client,register,mode,code):
 p=setup(client,register);e=equipment(client,p);data=b'not image' if mode!='oversize' else b'x'*(3*1024*1024+1)
 r=client.post(p+'/build/media',headers=csrf(client),data={'equipment_id':e['id'],'storage_consent':str(mode!='no_consent').lower()},files={'file':('photo.png',data,'text/html' if mode=='wrong_type' else 'image/png')});assert r.status_code==code,r.text
 assert client.get(p+'/build').json()['media']==[]

@pytest.mark.parametrize('intent',['inspect','question'])
def test_provider_receives_real_step_context_and_saved_photos_and_retains_review(client,register,monkeypatch,intent):
 p=setup(client,register);e=equipment(client,p);plan(client,p);b=session(client,p,'start');sid=b['session']['current_step_id'];mids=[photo(client,p,step_id=sid).json()['id'] for _ in range(2)];consent(client);captured=[]
 def provider(req):
  captured.append(json.loads(req.content));return httpx.Response(200,json={'id':'EXPLICIT-MOCK-COPILOT','model':'muse-spark-1.3','choices':[{'message':{'content':'## Visible observations\nSynthetic frame.\n## Cannot verify\nElectrical safety.\n## Next check\nRead the actual label.'}}]})
 fake_provider(monkeypatch,provider)
 body={'question':'Check my current step','copilot':True,'intent':intent,'build_step_id':sid,'equipment_id':e['id'],'media_ids':mids,'consent':True,'image_consent':False}
 assert client.post(p+'/ai/ask',headers=csrf(client),json=body).status_code==403
 body['image_consent']=True;r=client.post(p+'/ai/ask',headers=csrf(client),json=body);assert r.status_code==200,r.text
 assert r.json()['build_step_id']==sid and r.json()['media_ids']==mids
 content=captured[0]['messages'][-1]['content'];assert len([x for x in content if x['type']=='image_url'])==2
 assert 'Camera from label' in content[0]['text'] and 'Identify your available equipment' in content[0]['text']
 b=client.get(p+'/build').json();assert b['session']['status']=='NEEDS_REVIEW' and b['completed_steps']==0 and b['messages'][-1]['provider_id']=='EXPLICIT-MOCK-COPILOT'

def test_provider_failure_and_media_delete_do_not_grant_completion(client,register,monkeypatch):
 p=setup(client,register);plan(client,p);b=session(client,p,'start');sid=b['session']['current_step_id'];mid=photo(client,p,step_id=sid).json()['id'];consent(client)
 fake_provider(monkeypatch,lambda req:httpx.Response(401,json={'error':'private upstream credential detail'}))
 r=client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Check my work','copilot':True,'intent':'inspect','media_ids':[mid],'consent':True,'image_consent':True});assert r.status_code==502 and 'private upstream' not in r.text
 b=client.get(p+'/build').json();assert not b['messages'] and b['session']['status']=='IN_PROGRESS'
 session(client,p,'confirm',attestation=True,checks_confirmed=True,notes='Independent unpowered label check recorded.');session(client,p,'complete')
 assert client.delete(p+'/build/media/'+mid,headers=csrf(client)).status_code==204
 assert client.get(p+'/build').json()['steps'][0]['progress']['status']=='NEEDS_MORE_EVIDENCE'
 assert client.get(p+'/build/media/'+mid).status_code==404
 assert client.delete(p,headers=csrf(client)).status_code==204

def test_meta_plan_proposal_requires_review_and_retains_provenance(client,register,monkeypatch):
 p=setup(client,register);equipment(client,p);consent(client)
 draft={'steps':[{'objective':'Read camera label','instruction':'Read the label with all power disconnected.','component_ids':['camera'],'checks':['Record the exact revision'],'mistakes':['Guessing ratings'],'safety':'No power.','evidence_required':True}]}
 fake_provider(monkeypatch,lambda req:httpx.Response(200,json={'id':'MOCK-PLAN-PROPOSAL','model':'muse-spark-1.3','choices':[{'message':{'content':json.dumps(draft)}}]}))
 r=client.post(p+'/build/plan/proposal',headers=csrf(client),json={'consent':True});assert r.status_code==200,r.text
 assert not client.get(p+'/build').json()['steps']
 proposed=r.json();assert proposed['state']=='USER_REVIEW_REQUIRED'
 r=client.post(p+'/build/plan',headers=csrf(client),json={'steps':proposed['steps'],'proposal_message_id':proposed['message']['id']});assert r.status_code==201,r.text
 assert r.json()['plan_origin']=='USER_REVIEWED_PROVIDER_PROPOSAL'
 assert r.json()['steps'][0]['progress']['status']=='NOT_STARTED'

@pytest.mark.parametrize('answer',['not JSON',json.dumps({'steps':[{'objective':'Bad scope','instruction':'Wrong component reference','component_ids':['another-project-part']} ]})])
def test_invalid_provider_plan_never_changes_saved_steps(client,register,monkeypatch,answer):
 p=setup(client,register);consent(client)
 fake_provider(monkeypatch,lambda req:httpx.Response(200,json={'id':'MOCK-INVALID-PLAN','choices':[{'message':{'content':answer}}]}))
 assert client.post(p+'/build/plan/proposal',headers=csrf(client),json={'consent':True}).status_code==502
 b=client.get(p+'/build').json();assert not b['steps'] and not b['messages']

def test_late_image_response_cannot_overwrite_newer_user_checkpoint(client,register,monkeypatch):
 p=setup(client,register);plan(client,p);b=session(client,p,'start');mid=photo(client,p,step_id=b['session']['current_step_id']).json()['id'];consent(client)
 def provider(req):
  session(client,p,'status',status='BLOCKED',notes='A newer independent safety issue requires review.')
  return httpx.Response(200,json={'id':'MOCK-LATE-RESPONSE','choices':[{'message':{'content':'Possible visible issue; needs independent review.'}}]})
 fake_provider(monkeypatch,provider)
 r=client.post(p+'/ai/ask',headers=csrf(client),json={'question':'Check my work','copilot':True,'intent':'inspect','media_ids':[mid],'consent':True,'image_consent':True});assert r.status_code==200,r.text
 b=client.get(p+'/build').json();assert b['session']['status']=='BLOCKED' and b['steps'][0]['progress']['notes']=='A newer independent safety issue requires review.'
 assert b['messages'][-1]['provider_id']=='MOCK-LATE-RESPONSE'

def test_changed_assembly_reference_reopens_confirmation_and_is_exported(client,register):
 p=setup(client,register);plan(client,p,[{'objective':'Inspect camera','instruction':'Inspect the camera mount while disconnected.','component_ids':['camera']}]);session(client,p,'start');session(client,p,'confirm',attestation=True,checks_confirmed=True,notes='Independent mount support check completed.');session(client,p,'complete')
 workspace=client.get(p+'/workbench').json();workspace['data']['parts'][1]['x']=1
 assert client.put(p+'/workbench',headers=csrf(client),json={'expected_revision':workspace['revision'],**workspace['data']}).status_code==200
 b=client.get(p+'/build').json();assert b['session']['status']=='NEEDS_REVIEW' and b['completed_steps']==0
 exported=client.get('/api/account/export').json()['projects'][0]['my_build_memory'];assert exported['session']['status']=='NEEDS_REVIEW' and exported['steps'][0]['progress']['notes']=='Independent mount support check completed.'

def test_older_conversation_cursor_preserves_full_private_history(client,register):
 from datetime import datetime,timedelta,timezone
 from app.api import app
 from app.db import get_db
 from app.workbench_models import ChatMessage
 p=setup(client,register);pid=p.split('/')[-1];uid=client.get('/api/auth/me').json()['id']
 dependency=app.dependency_overrides[get_db]();db=next(dependency)
 try:
  at=datetime.now(timezone.utc)
  for i in range(53):db.add(ChatMessage(project_id=pid,user_id=uid,question=f'Pagination fixture {i}',answer='Explicit seeded test record',model='TEST_FIXTURE',provider_id='TEST_FIXTURE',context_version=1,sources=[],image_included=False,created_at=at+timedelta(seconds=i)))
  db.commit()
 finally:dependency.close()
 recent=client.get(p+'/ai/messages').json();assert len(recent)==50 and recent[0]['question']=='Pagination fixture 3'
 older=client.get(p+'/ai/messages',params={'before_id':recent[0]['id']}).json();assert [m['question'] for m in older]==['Pagination fixture 0','Pagination fixture 1','Pagination fixture 2']
 assert client.get(p+'/ai/messages',params={'before_id':'unknown'}).status_code==404

def test_deleted_equipment_author_does_not_leave_orphaned_project_photos(client,register):
 p=setup(client,register);owner=dict(client.cookies);register(client,'inventory-author@example.com');editor=dict(client.cookies)
 client.cookies.clear();client.cookies.update(owner);client.put(p+'/members',headers=csrf(client),json={'email':'inventory-author@example.com','role':'editor'})
 client.cookies.clear();client.cookies.update(editor);e=equipment(client,p)
 client.cookies.clear();client.cookies.update(owner);mid=photo(client,p,equipment_id=e['id']).json()['id']
 client.cookies.clear();client.cookies.update(editor);assert client.delete('/api/account',headers=csrf(client)).status_code==200
 client.cookies.clear();client.cookies.update(owner);b=client.get(p+'/build').json();assert not b['equipment'] and not b['media'];assert client.get(p+'/build/media/'+mid).status_code==404
