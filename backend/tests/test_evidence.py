"""Audit events are real application activity, never physical sensor evidence."""
from tests.conftest import csrf

def test_event_timeline_is_real_and_not_physical(client,register):
    register(client)
    p=client.post('/api/projects',json={'name':'Audit project'},headers=csrf(client)).json()
    pid=p['id']
    r=client.get(f'/api/projects/{pid}/evidence')
    assert r.status_code==200
    data=r.json()
    assert data['state']=='ACCOUNT_ACTIVITY_ONLY'
    assert data['physical_observations']==0
    assert data['events'][0]['description']=='Project created'
    assert data['events'][0]['physical_verification']=='NOT_ASSESSED'
    client.post(f'/api/projects/{pid}/engineering-plans',json={'family':'generic','goal':'Observe a safe voltage indicator'},headers=csrf(client))
    data=client.get(f'/api/projects/{pid}/evidence').json()
    assert any(e['event_type']=='plan.draft.created' for e in data['events'])
    assert all(e['evidence_kind']=='ACCOUNT_ACTIVITY' for e in data['events'])
    register(client,'different@example.com')
    assert client.get(f'/api/projects/{pid}/evidence').status_code==404
