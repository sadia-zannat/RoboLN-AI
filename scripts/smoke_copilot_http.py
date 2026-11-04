"""Real production frontend/API/database journey, explicit test-only Meta transport.
Includes real backend process restart and retained login/build/media/checkpoint data.
"""
import io,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
import httpx
from PIL import Image
from smoke_fullstack_http import free_port
ROOT=Path(__file__).resolve().parents[1]

def main():
    api_port,web_port=free_port(),free_port()
    while api_port==web_port:web_port=free_port()
    origin=f'http://127.0.0.1:{web_port}'
    checks=0
    with tempfile.TemporaryDirectory(prefix='roboln-copilot-http-') as temp:
        env={**os.environ,'ROBOLN_DATABASE_URL':'sqlite:///'+(Path(temp)/'qa.db').as_posix(),'ROBOLN_BACKEND_URL':f'http://127.0.0.1:{api_port}','ROBOLN_ALLOWED_ORIGINS':origin,'ROBOLN_COOKIE_SECURE':'false','MODEL_API_KEY':'','ROBOLN_TEST_API_PORT':str(api_port),'NEXT_TELEMETRY_DISABLED':'1'}
        subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT/'backend',env=env,check=True,capture_output=True)
        def start_api():return subprocess.Popen([sys.executable,'-m','tests.mock_provider_api'],cwd=ROOT/'backend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        backend=start_api()
        frontend=subprocess.Popen([shutil.which('node') or 'node',str(ROOT/'frontend/node_modules/next/dist/bin/next'),'start','--hostname','127.0.0.1','--port',str(web_port)],cwd=ROOT/'frontend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            with httpx.Client(base_url=origin,trust_env=False,timeout=15,headers={'origin':origin}) as c:
                def wait_ready():
                    for _ in range(100):
                        if backend.poll() is not None or frontend.poll() is not None:raise RuntimeError('Server exited before readiness')
                        try:
                            if c.get('/api/ready').status_code==200:return
                        except httpx.HTTPError:pass
                        time.sleep(.1)
                    raise RuntimeError('Bounded server startup expired')
                wait_ready()
                def ok(r,code=200):
                    nonlocal checks
                    assert r.status_code==code,(r.request.method,r.request.url.path,r.status_code,r.text[:300]);checks+=1
                    return r.json() if code!=204 else None
                def write(path,data,method='POST',code=200,client=c):return ok(client.request(method,'/api'+path,headers={'x-csrf-token':client.cookies['roboln_csrf']},json=data),code)
                def state():return ok(c.get('/api'+p+'/build'))
                def action(kind='save',**extra):
                    b=state();return write(p+'/build/session',{'expected_revision':b['session']['revision'],'action':kind,**extra},'PUT')
                def photo(**fields):
                    o=io.BytesIO();Image.new('RGB',(24,16),'blue').save(o,format='PNG')
                    return ok(c.post('/api'+p+'/build/media',headers={'x-csrf-token':c.cookies['roboln_csrf']},data={'storage_consent':'true',**fields},files={'file':('synthetic-http.png',o.getvalue(),'image/png')}),201)
                ok(c.post('/api/auth/register',json={'full_name':'Copilot TCP owner','email':'owner@copilot.example','password':'CopilotTcpPassword123!'}),201)
                project=write('/projects',{'name':'Restart-safe copilot rover','goal':'Review an unpowered camera assembly'},code=201);p='/projects/'+project['id']
                write(p+'/workbench',{'expected_revision':0,'parts':[{'id':'frame','name':'Frame','kind':'chassis','y':1},{'id':'camera','name':'Camera','kind':'camera','parent_id':'frame','y':2}]},'PUT')
                e=write(p+'/equipment',{'name':'Unpowered camera from label','category':'camera','bom_component_id':'camera','unknown_specs':'Exact supply rating'},code=201)
                photo(equipment_id=e['id']);photo(equipment_id=e['id'])
                b=state();assert len(b['equipment'][0]['photos'])==2 and b['missing_parts'][0]['name']=='Frame'
                write('/consents/cloud_ai',{'enabled':True},'PUT')
                proposal=write(p+'/build/plan/proposal',{'consent':True});assert proposal['message']['provider_id'].startswith('EXPLICIT-TEST-MOCK-')
                assert not state()['steps']
                b=write(p+'/build/plan',{'steps':proposal['steps'],'proposal_message_id':proposal['message']['id']},code=201)
                assert b['plan_origin']=='USER_REVIEWED_PROVIDER_PROPOSAL'
                b=action('start',selected_component_id='camera');sid=b['session']['current_step_id'];mid=photo(step_id=sid)['id']
                body={'copilot':True,'intent':'inspect','question':'Check the visible placement of the current camera step','build_step_id':sid,'equipment_id':e['id'],'media_ids':[mid],'consent':True,'image_consent':False}
                write(p+'/ai/ask',body,code=403);body['image_consent']=True
                review=write(p+'/ai/ask',body);assert 'EXPLICIT TEST MOCK' in review['answer'] and review['build_step_id']==sid
                b=state();assert b['session']['status']=='NEEDS_REVIEW' and b['completed_steps']==0
                action('confirm',checks_confirmed=True,attestation=True,notes='Independent software-fixture check; no physical measurement.')
                b=action('complete');assert b['completed_steps']==1
                b=action('go',step_id=b['steps'][1]['id'],selected_component_id='camera')
                b=action(notes='Checkpoint survives actual process restart.',experience='advanced',unresolved_issues=['Verify supply voltage independently.'])
                next_step=b['session']['current_step_id'];revision=b['session']['revision'];assert b['checkpoints']
                image=c.get('/api'+p+'/build/media/'+mid);assert image.status_code==200 and image.headers['content-type'].startswith('image/jpeg');checks+=1
                response=c.get(p+'/workspace/copilot');assert response.status_code==200 and 'text/html' in response.headers['content-type'];checks+=1
                backend.terminate();backend.wait(timeout=5)
                failed=c.get('/api'+p+'/build');ok(failed,502)
                backend=start_api();wait_ready()
                b=state();assert b['session']['current_step_id']==next_step and b['session']['revision']==revision
                assert b['session']['experience']=='advanced' and b['completed_steps']==1 and len(b['media'])==3
                assert b['steps'][1]['progress']['notes']=='Checkpoint survives actual process restart.' and b['messages'][-1]['provider_id'].startswith('EXPLICIT-TEST-MOCK-')
                assert ok(c.get('/api/auth/me'))['email']=='owner@copilot.example'
                write('/auth/logout',{});ok(c.get('/api'+p+'/build'),401)
                ok(c.post('/api/auth/login',json={'email':'owner@copilot.example','password':'CopilotTcpPassword123!'}))
                assert state()['session']['current_step_id']==next_step
                other=write('/projects',{'name':'Separate isolated project'},code=201);other_path='/projects/'+other['id']
                assert not ok(c.get('/api'+other_path+'/build'))['messages'];ok(c.get('/api'+other_path+'/build/media/'+mid),404)
                with httpx.Client(base_url=origin,trust_env=False,timeout=15,headers={'origin':origin}) as viewer:
                    ok(viewer.post('/api/auth/register',json={'full_name':'Copilot viewer','email':'viewer@copilot.example','password':'CopilotTcpPassword123!'}),201)
                    ok(viewer.get('/api'+p+'/build'),404)
                    write(p+'/members',{'email':'viewer@copilot.example','role':'viewer'},'PUT')
                    shared=ok(viewer.get('/api'+p+'/build'));assert shared['session']['status']=='NOT_STARTED' and not shared['checkpoints'] and not shared['messages']
                    write(p+'/build/session',{'expected_revision':0,'action':'start'},'PUT',403,viewer)
                    write(p+'/ai/ask',body,code=403,client=viewer)
                d=write(p+'/devices',{'name':'Explicit simulation fixture','adapter':'GENERIC_HTTP','mode':'SIMULATION'},code=201)
                write(p+'/twin/mappings',{'device_id':d['id'],'component_id':'camera','measurement':'soil_moisture','unit':'%'},code=201)
                ok(c.post('/api/device/telemetry',headers={'Authorization':'Bearer '+d['device_token']},json={'packet_id':'copilot-simulation','observed_at':datetime.now(timezone.utc).isoformat(),'measurements':[{'name':'soil_moisture','value':31.25,'unit':'%'}]}),201)
                twin=ok(c.get('/api'+p+'/twin/snapshot'));assert twin['component_states'][0]['origin']=='SIMULATION' and not twin['component_states'][0]['live_eligible']
                exported=ok(c.get('/api/account/export'));mine=next(x for x in exported['projects'] if x['id']==project['id']);assert mine['my_build_memory']['session']['current_step_id']==next_step and 'EXPLICIT_TEST_ONLY_NOT_A_REAL_KEY' not in str(exported)
                print(f'Copilot production Next -> real API -> SQLite: {checks} HTTP checks PASS, including actual backend termination/restart, saved steps, two equipment photos, scoped snapshot inspection via EXPLICIT TEST HTTP mock, user confirmation, checkpoint, relogin, project/member isolation, export and SIMULATION telemetry. No live Meta, physical camera, speech or hardware verification.')
        finally:
            for proc in [frontend,backend]:
                if proc.poll() is None:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':main()
