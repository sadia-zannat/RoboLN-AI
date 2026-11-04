"""Release regressions. Provider calls use an explicit HTTP mock; no live inference."""
import json
import httpx
import pytest
from tests.conftest import csrf
from tests.test_workbench import project, consent, fake_provider


@pytest.mark.parametrize('response', [None, [], 'invalid object', {'data': None}, {'data': {}}])
def test_malformed_model_catalog_is_a_structured_provider_failure(client, register, monkeypatch, response):
    register(client)
    consent(client)
    fake_provider(monkeypatch, lambda req: httpx.Response(200, content=json.dumps(response), headers={'content-type': 'application/json'}))
    r = client.post('/api/ai/check', headers=csrf(client), json={'consent': True})
    assert r.status_code == 502, r.text
    assert 'unit-test-provider-secret' not in r.text


def test_valid_model_catalog_reports_access_without_claiming_inference(client, register, monkeypatch):
    register(client)
    consent(client)
    fake_provider(monkeypatch, lambda req: httpx.Response(200, json={'data': [{'id': 'muse-spark-1.3'}]}))
    r = client.post('/api/ai/check', headers=csrf(client), json={'consent': True})
    assert r.status_code == 200, r.text
    assert r.json() == {'models': ['muse-spark-1.3'], 'configured_model_available': True, 'inference_verified': False}


def test_conversation_history_and_provider_context_are_scoped_to_project_and_author(client, register, monkeypatch):
    register(client)
    first = project(client, 'First release project')
    second = project(client, 'Second release project')
    consent(client)
    captured = []

    def provider(req):
        captured.append(json.loads(req.content))
        return httpx.Response(200, json={'id': f'mock-release-{len(captured)}', 'model': 'muse-spark-1.3',
            'choices': [{'message': {'content': f'Review-only answer {len(captured)}'}, 'finish_reason': 'stop'}]})

    fake_provider(monkeypatch, provider)
    def ask(path, question):
        r = client.post(path + '/ai/ask', headers=csrf(client), json={'question': question, 'consent': True})
        assert r.status_code == 200, r.text
        return r.json()

    a = ask(first, 'First project private question')
    ask(second, 'Second project private question')
    b = ask(first, 'Continue our first project discussion')
    history = client.get(first + '/ai/messages').json()
    assert [m['id'] for m in history] == [a['id'], b['id']]
    assert all(m['verification'] == 'REVIEW' for m in history)
    assert captured[2]['messages'][1:3] == [
        {'role': 'user', 'content': a['question']}, {'role': 'assistant', 'content': a['answer']}]
    assert 'Second project private question' not in json.dumps(captured[2])

    owner_cookies = dict(client.cookies)
    register(client, 'release-editor@example.com', 'Release Editor')
    editor_cookies = dict(client.cookies)
    client.cookies.clear()
    client.cookies.update(owner_cookies)
    granted = client.put(first + '/members', headers=csrf(client), json={'email': 'release-editor@example.com', 'role': 'editor'})
    assert granted.status_code == 200, granted.text
    client.cookies.clear()
    client.cookies.update(editor_cookies)
    assert client.get(first + '/ai/messages').json() == []
    assert client.get(second + '/ai/messages').status_code == 404
    consent(client)
    ask(first, 'Editor private engineering question')
    assert len(captured[-1]['messages']) == 2
    assert 'First project private question' not in json.dumps(captured[-1])
    client.cookies.clear()
    client.cookies.update(owner_cookies)
    assert [m['id'] for m in client.get(first + '/ai/messages').json()] == [a['id'], b['id']]
