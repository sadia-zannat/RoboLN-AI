"""Actual localhost Uvicorn smoke; never a TestClient emulation."""
import os, sys, time, socket, subprocess, pathlib, uuid
import httpx
root=pathlib.Path(__file__).resolve().parents[1]
backend=root/'backend'
port=18766
base=f'http://127.0.0.1:{port}'
(root/'logs').mkdir(exist_ok=True)
env={**os.environ,'ROBOLN_DATABASE_URL':'sqlite:///'+str(root/'logs'/('smoke_http_'+uuid.uuid4().hex[:10]+'.db'))}
subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=backend,env=env,check=True,stdout=subprocess.DEVNULL)
proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.api:app','--host','127.0.0.1','--port',str(port)],cwd=backend,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks=0
try:
  for i in range(50):
    try:
      r=httpx.get(base+'/api/health',timeout=.3,trust_env=False)
      if r.status_code==200:break
    except Exception:time.sleep(.15)
  else:raise RuntimeError('Uvicorn did not become ready')
  with httpx.Client(base_url=base,timeout=5,trust_env=False) as c:
    def verify(response,expected):
      global checks
      assert response.status_code==expected,(response.request.method,response.request.url,response.status_code,response.text)
      checks+=1
      return response
    verify(c.get('/api/health'),200)
    unique=uuid.uuid4().hex[:10]
    a=verify(c.post('/api/auth/register',json={'full_name':'HTTP smoke','email':f'smoke-{unique}@example.com','password':'SmokePass123456!'}),201)
    assert 'HttpOnly' in a.headers['set-cookie']
    verify(c.get('/api/auth/me'),200)
    verify(c.post('/api/projects',json={'name':'Not allowed without token'}),403)
    headers={'x-csrf-token':c.cookies.get('roboln_csrf')}
    p=verify(c.post('/api/projects',json={'name':'TCP Rover'},headers=headers),201).json()
    pid=p['id']
    verify(c.get(f'/api/projects/{pid}'),200)
    verify(c.get(f'/api/projects/{pid}/context'),200)
    verify(c.patch(f'/api/projects/{pid}',json={'name':'X'},headers=headers),422)
    verify(c.patch(f'/api/projects/{pid}',json={'name':'TCP Rover II','description':'','goal':''},headers=headers),200)
    verify(c.get(f'/api/projects/{pid}/twin'),200)
    verify(c.post('/api/auth/logout',headers=headers),200)
    verify(c.get(f'/api/projects/{pid}'),401)
    print('Uvicorn HTTP over TCP:',checks,'checks PASS, bind',base)
finally:
  proc.terminate()
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:proc.kill()
