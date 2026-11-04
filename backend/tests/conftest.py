import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path,monkeypatch):
    # Empty is intentional: dotenv must not reload a developer's paid key.
    monkeypatch.setenv('MODEL_API_KEY','')
    # Replace backing database and all prior module imports to ensure isolated app.
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from app.db import Base, get_db
    from app.api import app
    engine=create_engine(f'sqlite:///{tmp_path / "test.db"}',connect_args={'check_same_thread':False})
    @event.listens_for(engine,'connect')
    def fk(conn,_):conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    maker=sessionmaker(bind=engine,expire_on_commit=False)
    def override():
        with maker() as db:yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def register():
    def f(c,email='owner@example.com',name='Owner'):
        r=c.post('/api/auth/register',json={'email':email,'full_name':name,'password':'SafePasswordExample123!'})
        assert r.status_code==201,r.text
        return r.json()
    return f

def csrf(c): return {'x-csrf-token':c.cookies['roboln_csrf']}
