"""Real production Next proxy -> Uvicorn -> temporary SQLite integration checks.

This is HTTP integration coverage, not browser/UI, live provider or hardware QA.
Run with the pinned Python environment after `npm ci` and `npm run build`.
"""
import base64
import io
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    api_port, web_port = free_port(), free_port()
    while web_port == api_port:
        web_port = free_port()
    api_origin, web_origin = f'http://127.0.0.1:{api_port}', f'http://127.0.0.1:{web_port}'
    checks = 0
    with tempfile.TemporaryDirectory(prefix='roboln-fullstack-') as temp:
        env = {**os.environ, 'ROBOLN_DATABASE_URL': 'sqlite:///' + (Path(temp) / 'qa.db').as_posix(),
            'MODEL_API_KEY': '', 'ROBOLN_BACKEND_URL': api_origin, 'ROBOLN_ALLOWED_ORIGINS': web_origin,
            'ROBOLN_COOKIE_SECURE': 'false', 'NEXT_TELEMETRY_DISABLED': '1'}
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT / 'backend', env=env, check=True, capture_output=True)
        processes = []
        try:
            processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.api:app', '--host', '127.0.0.1', '--port', str(api_port)], cwd=ROOT / 'backend', env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            processes.append(subprocess.Popen([shutil.which('node') or 'node', str(ROOT / 'frontend/node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', str(web_port)], cwd=ROOT / 'frontend', env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            with httpx.Client(base_url=web_origin, trust_env=False, timeout=15, headers={'origin': web_origin}) as owner:
                for _ in range(100):
                    if any(p.poll() is not None for p in processes):
                        raise RuntimeError('A full-stack server exited before readiness')
                    try:
                        if owner.get('/api/ready').status_code == 200 and owner.get('/login').status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(.1)
                else:
                    raise RuntimeError('Production servers were not ready within the bounded startup window')

                def checked(response, expected=200):
                    nonlocal checks
                    assert response.status_code == expected, (response.request.method, response.request.url.path, response.status_code, response.text[:400])
                    checks += 1
                    return response.json() if response.status_code != 204 else None

                def headers(client):
                    return {'x-csrf-token': client.cookies['roboln_csrf']}

                def write(client, method, path, data, status=200):
                    return checked(client.request(method, '/api' + path, headers=headers(client), json=data), status)

                checked(owner.get('/api/auth/me'), 401)
                registered = owner.post('/api/auth/register', json={'full_name': 'Full-stack owner', 'email': 'owner@fullstack.example', 'password': 'FullStackTestingPassword123!'})
                checked(registered, 201)
                assert 'httponly' in registered.headers['set-cookie'].lower()
                assert registered.headers.get('x-roboln-request-id')
                checked(owner.post('/api/projects', json={'name': 'CSRF must reject'}), 403)
                project = write(owner, 'POST', '/projects', {'name': 'Full-stack persisted rover', 'goal': 'Software-only integration verification'}, 201)
                path = '/projects/' + project['id']
                write(owner, 'PUT', path + '/draft', {'draft': 'Saved through the real production proxy'})
                write(owner, 'PUT', path + '/hardware', {'board_model': 'Unverified test controller', 'device_class': 'SBC'})
                layout = {'expected_revision': 0, 'parts': [
                    {'id': 'frame', 'name': 'Provisional frame', 'kind': 'chassis', 'x': 1, 'y': 1},
                    {'id': 'sensor', 'name': 'Test soil probe', 'kind': 'sensor', 'parent_id': 'frame', 'x': 1.5, 'y': 2}]}
                write(owner, 'PUT', path + '/workbench', layout)
                write(owner, 'PUT', path + '/workbench', layout, 409)
                saved = checked(owner.get('/api' + path + '/workbench'))
                assert saved['data']['parts'][1]['parent_id'] == 'frame'
                assert saved['data']['parts'][1]['x'] == 1.5
                source = checked(owner.post('/api' + path + '/sources', headers=headers(owner), files={'file': ('reference.txt', b'Software QA calibration reference, not a physical measurement.')}), 201)
                found = checked(owner.get('/api' + path + '/sources/search', params={'q': 'calibration'}))
                assert found['results'][0]['source_id'] == source['id']
                image = io.BytesIO()
                Image.new('RGB', (12, 12), 'blue').save(image, format='PNG')
                observation = write(owner, 'POST', path + '/observations', {'title': 'Synthetic HTTP evidence', 'state': 'REVIEW',
                    'component_id': 'sensor', 'image_data_url': 'data:image/png;base64,' + base64.b64encode(image.getvalue()).decode(), 'storage_consent': True}, 201)
                image_response = owner.get('/api' + path + '/observations/' + observation['id'] + '/image')
                assert image_response.status_code == 200 and image_response.headers['content-type'].startswith('image/jpeg')
                checks += 1
                device = write(owner, 'POST', path + '/devices', {'name': 'Software producer', 'adapter': 'GENERIC_HTTP', 'mode': 'SIMULATION'}, 201)
                write(owner, 'POST', path + '/twin/mappings', {'device_id': device['id'], 'component_id': 'sensor', 'measurement': 'soil_moisture', 'unit': '%' }, 201)
                checked(owner.post('/api/device/telemetry', headers={'Authorization': 'Bearer ' + device['device_token']}, json={
                    'packet_id': 'fullstack-simulation-1', 'observed_at': datetime.now(timezone.utc).isoformat(),
                    'measurements': [{'name': 'soil_moisture', 'value': 34.25, 'unit': '%'}]}), 201)
                twin = checked(owner.get('/api' + path + '/twin/snapshot'))
                reading = twin['component_states'][0]
                assert reading['value'] == 34.25 and reading['origin'] == 'SIMULATION' and not reading['live_eligible']
                write(owner, 'PUT', '/consents/cloud_ai', {'enabled': True})
                write(owner, 'POST', path + '/ai/ask', {'question': 'Review my saved engineering context', 'consent': True}, 503)
                assert checked(owner.get('/api' + path + '/ai/messages')) == []
                write(owner, 'PATCH', '/preferences/theme', {'theme': 'dark'})
                write(owner, 'POST', '/auth/logout', {})
                checked(owner.get('/api' + path), 401)
                checked(owner.post('/api/auth/login', json={'email': 'owner@fullstack.example', 'password': 'FullStackTestingPassword123!'}))
                assert checked(owner.get('/api/auth/me'))['theme'] == 'dark'
                assert checked(owner.get('/api' + path + '/draft'))['draft'] == 'Saved through the real production proxy'
                for suffix in ['', '/workspace/plan', '/workspace/practice', '/workspace/copilot', '/twin', '/evidence']:
                    response = owner.get(path + suffix)
                    assert response.status_code == 200 and 'text/html' in response.headers['content-type']
                    checks += 1
                exported = checked(owner.get('/api' + path + '/engineering-export'))
                assert exported['workspace']['revision'] == 1
                evidence = checked(owner.get('/api' + path + '/evidence'))
                assert evidence['physical_observations'] == 1
                with httpx.Client(base_url=web_origin, trust_env=False, timeout=15, headers={'origin': web_origin}) as viewer:
                    checked(viewer.post('/api/auth/register', json={'full_name': 'Viewer', 'email': 'viewer@fullstack.example', 'password': 'FullStackTestingPassword123!'}), 201)
                    checked(viewer.get('/api' + path), 404)
                    write(owner, 'PUT', path + '/members', {'email': 'viewer@fullstack.example', 'role': 'viewer'})
                    assert checked(viewer.get('/api' + path))['role'] == 'viewer'
                    write(viewer, 'PUT', path + '/workbench', {**layout, 'expected_revision': 1}, 403)
                    write(viewer, 'PUT', path + '/draft', {'draft': 'Unauthorized overwrite'}, 403)
                    assert checked(viewer.get('/api' + path + '/ai/messages')) == []
                print(f'Production Next.js -> FastAPI -> SQLite: {checks} HTTP checks PASS. Real cookies/CSRF, login, RBAC, saved layout/parents, sources, synthetic image/evidence, simulation telemetry, theme persistence and provider-not-configured path. HTML routes returned successfully; client rendering and browser interactions are NOT certified.')
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
