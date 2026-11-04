"""Real TCP-level FastAPI smoke; migrations use an isolated temp SQLite DB."""
import os,sys,tempfile,subprocess,time,json,urllib.request,urllib.error,http.cookiejar, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='roboln-real-http-plan-') as tmp:
    dbpath=pathlib.Path(tmp)/'db.sqlite'
    env={**os.environ,'ROBOLN_DATABASE_URL':'sqlite:///'+str(dbpath)}
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env,check=True,capture_output=True)
    port=18767
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.api:app','--host','127.0.0.1','--port',str(port)],cwd=root/'backend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        jar=http.cookiejar.CookieJar()
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(jar))
        checks=0
        def req(path,method='GET',data=None,csrf=False):
            nonlocal_placeholder=None
            headers={}
            if data is not None:headers['Content-Type']='application/json'
            if csrf:
                headers['x-csrf-token']=next(c.value for c in jar if c.name=='roboln_csrf')
            payload=json.dumps(data).encode() if data is not None else None
            response=opener.open(urllib.request.Request('http://127.0.0.1:'+str(port)+path,data=payload,headers=headers,method=method),timeout=15)
            try:return response.status,json.loads(response.read().decode())
            finally:response.close()
        for _ in range(50):
            try:
                assert req('/api/health')[0]==200;break
            except Exception:time.sleep(.1)
        else:raise AssertionError('API did not launch')
        checks+=1
        status,user=req('/api/auth/register','POST',{'email':'local-smoke@example.com','password':'SafePasswordExample123!','full_name':'Smoke User'})
        assert status==201;checks+=1
        status,p=req('/api/projects','POST',{'name':'HTTP planning smoke'},True)
        assert status==201;pid=p['id'];checks+=1
        status,plan=req(f'/api/projects/{pid}/engineering-plans','POST',{'family':'obstacle_alarm','goal':'Measure an obstacle distance for a safe indicator'},True)
        assert status==201 and plan['document']['verification']=='NOT_VERIFIED';checks+=1
        status,listing=req(f'/api/projects/{pid}/engineering-plans')
        assert status==200 and listing['plans'][0]['id']==plan['id'];checks+=1
        status,evidence=req(f'/api/projects/{pid}/evidence')
        assert status==200 and evidence['physical_observations']==0 and len(evidence['events'])==2;checks+=1
        status,export=req('/api/account/export')
        assert status==200 and export['projects'][0]['my_engineering_plan_revisions'][0]['id']==plan['id'];checks+=1
        print('REAL UVICORN TCP planning smoke: %d checks PASS; real SQLite migration; no model or physical hardware involved'%checks)
    finally:
        proc.terminate()
        try:proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:proc.kill();proc.communicate()
