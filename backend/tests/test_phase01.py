import pytest
from jsonschema import validate
from pathlib import Path
import json
from .conftest import csrf


def create(c,name='Rover alpha'):
    return c.post('/api/projects',json={'name':name,'description':'Real project'},headers=csrf(c))

def test_signup_login_csrf_logout(client,register):
    assert client.get('/api/auth/me').status_code==401
    u=register(client)
    assert client.get('/api/auth/me').json()['id']==u['id']
    assert client.post('/api/projects',json={'name':'Should fail'}).status_code==403
    assert client.post('/api/projects',json={'name':'Nope'},headers={'x-csrf-token':'wrong'}).status_code==403
    assert client.post('/api/projects',json={'name':'Nope'},headers={**csrf(client),'origin':'https://evil.example'}).status_code==403
    assert create(client).status_code==201
    assert client.post('/api/auth/logout',headers=csrf(client)).status_code==200
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':u['email'],'password':'wrong-password-long'}).status_code==401
    assert client.post('/api/auth/login',json={'email':u['email'],'password':'SafePasswordExample123!'}).status_code==200
    assert len(client.get('/api/projects').json())==1


def test_projects_crud_and_hardware_context(client,register):
    register(client)
    a=create(client)
    assert a.status_code==201,a.text
    pid=a.json()['id']
    assert client.get('/api/projects/'+pid).json()['name']=='Rover alpha'
    assert client.patch('/api/projects/'+pid,json={'name':'Smart Rover','description':'New','goal':'measure only'},headers=csrf(client)).status_code==200
    hw=client.put(f'/api/projects/{pid}/hardware',json={'device_class':'MCU','board_model':'ESP32-S3 user-provided','board_revision':'unverified','pin_map':{}},headers=csrf(client))
    assert hw.status_code==200,hw.text
    assert hw.json()['profile_review_state']=='REVIEW_REQUIRED'
    ctx=client.get(f'/api/projects/{pid}/context').json()
    schema=json.loads((Path(__file__).parents[2]/'packages/contracts/project_context.schema.json').read_text())
    validate(ctx,schema)
    assert ctx['context_version']==3
    assert ctx['hardware_profile_id']
    assert client.put(f'/api/projects/{pid}/draft',json={'draft':'Ask about sensor pins'},headers=csrf(client)).status_code==200
    assert client.get(f'/api/projects/{pid}/draft').json()['draft']=='Ask about sensor pins'
    assert client.post(f'/api/projects/{pid}/archive',headers=csrf(client)).json()['archived']
    assert client.delete(f'/api/projects/{pid}',headers=csrf(client)).status_code==204
    assert client.get(f'/api/projects/{pid}').status_code==404


def test_isolation_viewer_editor_owner(client,register):
    owner=register(client)
    a=create(client).json()['id']
    b=create(client,'Second private rover').json()['id']
    client.post('/api/auth/logout',headers=csrf(client))
    viewer=register(client,'viewer@example.com','Viewer')
    assert client.get(f'/api/projects/{a}').status_code==404
    assert client.get(f'/api/projects/{a}/hardware').status_code==404
    assert client.get(f'/api/projects/{b}/draft').status_code==404
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'})
    assert client.put(f'/api/projects/{a}/members',json={'email':viewer['email'],'role':'viewer'},headers=csrf(client)).status_code==200
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':viewer['email'],'password':'SafePasswordExample123!'})
    assert client.get(f'/api/projects/{a}').status_code==200
    assert client.get(f'/api/projects/{b}').status_code==404
    assert client.patch(f'/api/projects/{a}',json={'name':'Malicious'},headers=csrf(client)).status_code==403
    assert client.delete(f'/api/projects/{a}',headers=csrf(client)).status_code==403
    assert client.put(f'/api/projects/{a}/hardware',json={'board_model':'bad'},headers=csrf(client)).status_code==403
    assert client.put(f'/api/projects/{a}/draft',json={'draft':'should fail'},headers=csrf(client)).status_code==403
    assert client.get(f'/api/projects/{a}/evidence').json()['physical_observations']==0
    assert all(e['evidence_kind']=='ACCOUNT_ACTIVITY' for e in client.get(f'/api/projects/{a}/evidence').json()['events'])
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'})
    assert client.put(f'/api/projects/{a}/members',json={'email':viewer['email'],'role':'editor'},headers=csrf(client)).status_code==200
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email':viewer['email'],'password':'SafePasswordExample123!'})
    assert client.patch(f'/api/projects/{a}',json={'name':'Editor update'},headers=csrf(client)).status_code==200
    assert client.post(f'/api/projects/{a}/archive',headers=csrf(client)).status_code==403


def test_preferences_consents_export_delete(client,register):
    register(client)
    assert client.patch('/api/preferences/theme',json={'theme':'dark'},headers=csrf(client)).json()['theme']=='dark'
    assert client.put('/api/consents/camera',json={'enabled':True},headers=csrf(client)).json()['enabled']
    assert client.get('/api/consents').json()['camera']
    assert client.patch('/api/profile',json={'full_name':'New Name'},headers=csrf(client)).json()['full_name']=='New Name'
    p=create(client).json()['id']
    exported=client.get('/api/account/export').json()
    assert exported['projects'][0]['id']==p
    assert exported['consents']['camera'] is True
    assert client.delete('/api/account',headers=csrf(client)).json()['deleted']
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':'owner@example.com','password':'SafePasswordExample123!'}).status_code==401


def test_negative_inputs_and_trust_boundary(client,register):
    register(client)
    assert create(client,'a').status_code==422
    assert client.get('/api/projects/00000000-0000-0000-0000-000000000000').status_code==404
    assert client.put('/api/consents/nonexistent',json={'enabled':True},headers=csrf(client)).status_code==422
    assert client.put('/api/projects/anything/hardware',json={'device_class':'ROCKET'},headers=csrf(client)).status_code==422
    assert client.get('/api/health').json()['telemetry']=='AUTHENTICATED_INGESTION'


def test_login_throttle_is_db_persistent(client,register):
    register(client)
    client.post('/api/auth/logout',headers=csrf(client))
    for _ in range(5):
        assert client.post('/api/auth/login',json={'email':'owner@example.com','password':'WrongPassword123!'}).status_code==401
    assert client.post('/api/auth/login',json={'email':'owner@example.com','password':'SafePasswordExample123!'}).status_code==429


def test_whitespace_names_and_bounded_hardware_are_rejected(client, register):
    register(client)
    pid=create(client).json()['id']
    assert client.patch(f'/api/projects/{pid}', json={'name':'     '},headers=csrf(client)).status_code==422
    assert client.patch('/api/profile',json={'full_name':'   '},headers=csrf(client)).status_code==422
    oversize={f'pin{i}':'value' for i in range(101)}
    assert client.put(f'/api/projects/{pid}/hardware',json={'pin_map':oversize},headers=csrf(client)).status_code==422
    assert client.get(f'/api/projects/{pid}').json()['name']=='Rover alpha'

def test_archived_project_is_read_only_until_restored(client, register):
    register(client)
    pid=create(client).json()['id']
    assert client.post(f'/api/projects/{pid}/archive',headers=csrf(client)).status_code==200
    assert client.patch(f'/api/projects/{pid}',json={'name':'Should not save'},headers=csrf(client)).status_code==409
    assert client.put(f'/api/projects/{pid}/hardware',json={'board_model':'Should not save'},headers=csrf(client)).status_code==409
    assert client.post(f'/api/projects/{pid}/archive',headers=csrf(client)).status_code==200
    assert client.patch(f'/api/projects/{pid}',json={'name':'Restored'},headers=csrf(client)).status_code==200


def test_archive_blocks_membership_changes_and_preserves_existing_members(client, register):
    owner = register(client)
    pid = create(client).json()['id']
    client.post('/api/auth/logout', headers=csrf(client))
    viewer = register(client, 'archive-viewer@example.com', 'Archive viewer')
    client.post('/api/auth/logout', headers=csrf(client))
    client.post('/api/auth/login', json={'email': owner['email'], 'password': 'SafePasswordExample123!'})
    assert client.put(f'/api/projects/{pid}/members', json={'email': viewer['email'], 'role':'viewer'}, headers=csrf(client)).status_code == 200
    assert client.post(f'/api/projects/{pid}/archive', headers=csrf(client)).status_code == 200
    assert client.put(f'/api/projects/{pid}/members', json={'email': viewer['email'], 'role':'editor'}, headers=csrf(client)).status_code == 409
    assert client.delete(f'/api/projects/{pid}/members/{viewer["id"]}', headers=csrf(client)).status_code == 409
    assert any(m['id'] == viewer['id'] and m['role'] == 'viewer' for m in client.get(f'/api/projects/{pid}/members').json())
    assert client.post(f'/api/projects/{pid}/archive', headers=csrf(client)).status_code == 200
    assert client.put(f'/api/projects/{pid}/members', json={'email': viewer['email'], 'role':'editor'}, headers=csrf(client)).status_code == 200


def test_create_rejects_whitespace_short_name_and_oversized_sensor_draft(client, register):
    register(client)
    for name in [' a', 'a ', '   ', '\nA\t']:
        assert create(client, name).status_code == 422
    pid = create(client, 'Real Project').json()['id']
    inventory = [{'model': 'Unverified', 'notes': 'z' * 35_000}]
    result = client.put(f'/api/projects/{pid}/hardware', json={'sensor_inventory': inventory}, headers=csrf(client))
    assert result.status_code == 422, result.text
    assert client.get(f'/api/projects/{pid}/hardware').json() is None


def test_cross_project_privacy_covers_drafts_hardware_context_twin_export(client, register):
    account_a = register(client)
    pid = create(client, 'Private project A').json()['id']
    assert client.put(f'/api/projects/{pid}/draft',json={'draft':'Private hardware plan'},headers=csrf(client)).status_code == 200
    assert client.put(f'/api/projects/{pid}/hardware',json={'board_model':'Private MCU'},headers=csrf(client)).status_code == 200
    client.post('/api/auth/logout',headers=csrf(client))
    register(client,'account-b@example.com','Account B')
    for suffix in ['', '/draft', '/hardware', '/members', '/context', '/evidence', '/twin']:
        assert client.get(f'/api/projects/{pid}{suffix}').status_code == 404
    assert pid not in str(client.get('/api/account/export').json())
    assert client.put(f'/api/projects/{pid}/draft',json={'draft':'overwrite'},headers=csrf(client)).status_code == 404
    assert client.put(f'/api/projects/{pid}/hardware',json={'board_model':'overwrite'},headers=csrf(client)).status_code == 404
    assert client.delete(f'/api/projects/{pid}',headers=csrf(client)).status_code == 404
    client.post('/api/auth/logout',headers=csrf(client))
    client.post('/api/auth/login',json={'email': account_a['email'],'password':'SafePasswordExample123!'})
    assert client.get(f'/api/projects/{pid}/draft').json()['draft'] == 'Private hardware plan'


def test_account_export_includes_my_hardware_drafts_and_audit_but_no_other_members_draft(client, register):
    owner = register(client)
    pid = create(client, 'Export scope').json()['id']
    my_hw = {'device_class':'SBC','board_model':'Pi 3 Model B+', 'board_revision':'1.2', 'pin_map':{'demo':'unverified'}}
    assert client.put(f'/api/projects/{pid}/hardware',json=my_hw,headers=csrf(client)).status_code == 200
    assert client.put(f'/api/projects/{pid}/draft',json={'draft':'owner private build notes'},headers=csrf(client)).status_code == 200
    client.post('/api/auth/logout',headers=csrf(client))
    collaborator=register(client,'collaborator@example.com','Collaborator')
    client.post('/api/auth/logout',headers=csrf(client))
    assert client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'}).status_code==200
    assert client.put(f'/api/projects/{pid}/members',json={'email':collaborator['email'],'role':'editor'},headers=csrf(client)).status_code==200
    client.post('/api/auth/logout',headers=csrf(client))
    assert client.post('/api/auth/login',json={'email':collaborator['email'],'password':'SafePasswordExample123!'}).status_code==200
    assert client.put(f'/api/projects/{pid}/draft',json={'draft':'collaborator secret notes'},headers=csrf(client)).status_code==200
    editor_export=client.get('/api/account/export')
    assert editor_export.status_code==200
    assert editor_export.headers['cache-control']=='no-store'
    editor_project=editor_export.json()['projects'][0]
    assert editor_project['my_draft']=='collaborator secret notes'
    assert editor_project['hardware_draft']['board_model']=='Pi 3 Model B+'
    assert 'owner private build notes' not in editor_export.text
    client.post('/api/auth/logout',headers=csrf(client))
    assert client.post('/api/auth/login',json={'email':owner['email'],'password':'SafePasswordExample123!'}).status_code==200
    owner_export=client.get('/api/account/export')
    assert owner_export.json()['projects'][0]['my_draft']=='owner private build notes'
    assert 'collaborator secret notes' not in owner_export.text
    assert 'password_hash' not in owner_export.text
    assert 'roboln_session' not in owner_export.text
    assert any(e['action']=='hardware.draft' and e['project_id']==pid for e in owner_export.json()['my_audit_events'])
    assert client.delete(f'/api/projects/{pid}',headers=csrf(client)).status_code==204
    assert pid not in [p['id'] for p in client.get('/api/account/export').json()['projects']]


def test_api_response_security_headers_cover_authenticated_and_error_responses(client,register):
    anonymous=client.get('/api/projects')
    assert anonymous.status_code==401
    for name,value in {'cache-control':'no-store', 'x-content-type-options':'nosniff',
                       'referrer-policy':'no-referrer','x-frame-options':'DENY'}.items():
        assert anonymous.headers[name] == value
    register(client)
    project=create(client)
    assert project.status_code==201
    assert project.headers['cache-control']=='no-store'
    assert client.get('/api/projects').headers['cache-control']=='no-store'
    assert client.get('/api/account/export').headers['cache-control']=='no-store'
