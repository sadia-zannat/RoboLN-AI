"""Execute real localhost API + Python device bridge. All sensor data are SIMULATION."""
import json,os,pathlib,subprocess,sys,tempfile,time
import httpx
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='roboln-workbench-http-') as tmp:
    base='http://127.0.0.1:18768'
    env={**os.environ,'ROBOLN_DATABASE_URL':'sqlite:///'+str(pathlib.Path(tmp)/'test.db'),'MODEL_API_KEY':''}
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env,check=True,capture_output=True)
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.api:app','--host','127.0.0.1','--port','18768'],cwd=root/'backend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    checks=0
    try:
        with httpx.Client(base_url=base,trust_env=False,timeout=10) as c:
            for _ in range(60):
                try:
                    if c.get('/api/ready').status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(.1)
            else:raise RuntimeError('API did not become ready')
            def ok(r,code=200):
                global checks
                assert r.status_code==code,(r.status_code,r.text);checks+=1;return r.json() if code!=204 else None
            ok(c.post('/api/auth/register',json={'full_name':'TCP QA','email':'tcp@example.com','password':'SoftwareTcpQa123!'}),201)
            headers={'x-csrf-token':c.cookies['roboln_csrf']}
            p=ok(c.post('/api/projects',headers=headers,json={'name':'TCP integrated workbench'}),201);path='/api/projects/'+p['id']
            s=ok(c.post(path+'/sources',headers=headers,files={'file':('reference.txt',b'Calibration evidence must use physical dry and wet soil samples.')}),201)
            result=ok(c.get(path+'/sources/search',params={'q':'calibration'}));assert result['results'][0]['source_id']==s['id']
            ok(c.put(path+'/workbench',headers=headers,json={'expected_revision':0,'parts':[{'id':'sensor','name':'Moisture sensor','kind':'sensor','source_id':s['id']}]}))
            ok(c.post(path+'/observations',headers=headers,json={'title':'Software QA observation','notes':'No physical evidence; API test only','state':'UNKNOWN','component_id':'sensor'}),201)
            d=ok(c.post(path+'/devices',headers=headers,json={'name':'Software packet producer','adapter':'RASPBERRY_PI','mode':'SIMULATION'}),201)
            packet=pathlib.Path(tmp)/'sample.json';packet.write_text(json.dumps({'measurements':[{'name':'soil_moisture','value':41.25,'unit':'%'}],'event':'Explicit software simulation; no physical sensor'}))
            adapter_env={**env,'ROBOLN_API_URL':base,'ROBOLN_DEVICE_TOKEN':d['device_token'],'NO_PROXY':'127.0.0.1,localhost'}
            run=subprocess.run([sys.executable,str(root/'adapters/http_device.py'),'--expected-mode','SIMULATION','--input',str(packet)],env=adapter_env,text=True,capture_output=True,check=True)
            assert json.loads(run.stdout)['origin']=='SIMULATION';checks+=1
            mismatch=subprocess.run([sys.executable,str(root/'adapters/http_device.py'),'--expected-mode','LIVE_REAL','--input',str(packet)],env=adapter_env,text=True,capture_output=True)
            assert mismatch.returncode==1 and 'origin does not match' in mismatch.stderr;checks+=1
            twin=ok(c.get(path+'/twin'));assert twin['connection']=='SIMULATION' and twin['devices'][0]['latest']['measurements'][0]['value']==41.25
            assert len(ok(c.get(path+'/telemetry/history')))==1
            control=ok(c.post(path+'/controls',headers=headers,json={'device_id':d['id'],'action':'SAFE_STOP','reason':'Software test; hardware remains disconnected'}),201)
            reviewed=ok(c.post(path+'/controls/'+control['id']+'/review',headers=headers,json={'decision':'APPROVE','acknowledge':True}));assert reviewed['state']=='APPROVED_HOLD'
            assert ok(c.get('/api/ai/status'))['status']=='NOT_CONFIGURED'
            ok(c.post(path+'/devices/'+d['id']+'/revoke',headers=headers))
            ok(c.get('/api/device/status',headers={'Authorization':'Bearer '+d['device_token']}),401)
            ok(c.post('/api/auth/logout',headers=headers));ok(c.get(path),401)
            print(f'REAL UVICORN TCP integrated workbench: {checks} checks PASS; Python adapter executed; sensor packet explicitly SIMULATION; no provider/hardware inference.')
    finally:
        proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
