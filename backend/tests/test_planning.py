"""Real API scenarios: different projects, unknown hardware, restricted risk, and RBAC."""
from tests.conftest import csrf

def project(c,name):
    r=c.post('/api/projects',json={'name':name},headers=csrf(c));assert r.status_code==201,r.text
    return r.json()['id']
def create(c,pid,family,goal='Read the sensor and show a low-voltage indicator'):
    return c.post(f'/api/projects/{pid}/engineering-plans',json={'family':family,'goal':goal},headers=csrf(c))

def test_two_distinct_project_plans_and_no_fabricated_pinout(client,register):
    register(client)
    a=project(client,'Parking sensor')
    b=project(client,'Irrigation trainer')
    assert client.put(f'/api/projects/{a}/hardware',json={'device_class':'SBC','board_model':'Raspberry Pi 3 Model B+','board_revision':'1.3'},headers=csrf(client)).status_code==200
    ra=create(client,a,'obstacle_alarm');rb=create(client,b,'smart_irrigation')
    assert ra.status_code==rb.status_code==201
    x,y=ra.json(),rb.json()
    assert x['document']['board']=='Raspberry Pi 3 Model B+'
    assert y['document']['board'] is None
    assert x['document']['verification']=='NOT_VERIFIED'
    assert x['document']['model_provenance']['meta_model_inference'] is False
    assert 'datasheet' in ' '.join(x['document']['blockers']).lower()
    assert 'pin_map' not in str(x['document'])
    assert len(client.get(f'/api/projects/{a}/engineering-plans').json()['plans'])==1
    assert len(client.get(f'/api/projects/{b}/engineering-plans').json()['plans'])==1
    assert client.get(f'/api/projects/{a}/engineering-plans/{y["id"]}').status_code==404
    a2=create(client,a,'generic','Check the measurement and document the sensor constraints')
    assert a2.json()['revision']==2
    assert a2.json()['id']!=x['id']
    assert client.get(f'/api/projects/{a}/engineering-plans/{x["id"]}').json()['revision']==1

def test_restricted_goals_remain_concept_only(client,register):
    register(client);pid=project(client,'Demo concept')
    r=create(client,pid,'generic','Automatically operate a real railway crossing gate')
    assert r.status_code==201
    d=r.json()['document']
    assert d['mode']=='RESTRICTED_CONCEPT_ONLY'
    assert not d['candidate_parts']
    assert any('RESTRICTED_OPERATION' in x for x in d['blockers'])

def test_plan_access_csrf_archived_and_cross_user(client,register):
    register(client,'owner@example.com');pid=project(client,'Protected workspace')
    assert client.post(f'/api/projects/{pid}/engineering-plans',json={'family':'generic','goal':'Measure low voltage'}).status_code==403
    assert create(client,pid,'bogus').status_code==422
    c=create(client,pid,'generic');assert c.status_code==201
    client.post(f'/api/projects/{pid}/archive',headers=csrf(client))
    assert create(client,pid,'generic').status_code==409
    # second signed-in identity has no project membership
    register(client,'other@example.com')
    assert client.get(f'/api/projects/{pid}/engineering-plans').status_code==404
    assert create(client,pid,'generic').status_code==404
    assert client.get(f'/api/projects/{pid}/engineering-plans/{c.json()["id"]}').status_code==404

def test_planning_input_bounded(client,register):
    register(client);pid=project(client,'Length bounds')
    assert create(client,pid,'generic','  ').status_code==422
    assert client.post(f'/api/projects/{pid}/engineering-plans',json={'family':'generic','goal':'x'*1201},headers=csrf(client)).status_code==422
    assert client.get('/api/planning/families').json()['families']

def test_account_export_includes_only_my_authored_plan_revisions(client,register):
    owner=register(client)
    pid=project(client,'Collaborative plan export')
    authored=create(client,pid,'environment_monitor').json()
    client.post('/api/auth/logout',headers=csrf(client))
    editor=register(client,'editor@example.com','Editor')
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'})
    assert client.put(f'/api/projects/{pid}/members',json={'email':editor['email'],'role':'editor'},headers=csrf(client)).status_code==200
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':editor['email'],'password':'SafePasswordExample123!'})
    export=client.get('/api/account/export').json()
    assert export['projects'][0]['my_engineering_plan_revisions']==[]
    mine=create(client,pid,'generic').json()
    export=client.get('/api/account/export').json()
    assert [p['id'] for p in export['projects'][0]['my_engineering_plan_revisions']]==[mine['id']]
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'})
    export=client.get('/api/account/export').json()
    assert [p['id'] for p in export['projects'][0]['my_engineering_plan_revisions']]==[authored['id']]
