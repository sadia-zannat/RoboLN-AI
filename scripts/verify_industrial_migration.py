"""Real old-head database upgrade: preserve user/project/device/chat/packet and backfill readings."""
import os,subprocess,sys,tempfile,pathlib,json
from datetime import datetime,timezone
from sqlalchemy import create_engine,MetaData,Table,select,text
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='roboln-old-data-') as tmp:
    url='sqlite:///'+str(pathlib.Path(tmp)/'test.db');env={**os.environ,'ROBOLN_DATABASE_URL':url}
    def migrate(*args):subprocess.run([sys.executable,'-m','alembic',*args],cwd=root/'backend',env=env,check=True,capture_output=True)
    migrate('upgrade','25b229225e46');e=create_engine(url);meta=MetaData();meta.reflect(e);at=datetime.now(timezone.utc)
    with e.begin() as c:
        c.execute(meta.tables['users'].insert().values(id='u',email='migration@example.com',full_name='Preserved user',password_hash='test-only',theme='light',created_at=at))
        c.execute(meta.tables['projects'].insert().values(id='p',name='Preserved rover',description='',goal='',owner_id='u',context_version=1,archived=False,created_at=at))
        c.execute(meta.tables['memberships'].insert().values(project_id='p',user_id='u',role='owner'))
        c.execute(meta.tables['devices'].insert().values(id='d',project_id='p',name='Preserved device',adapter='GENERIC_HTTP',mode='SIMULATION',token_hash='hash-only-fixture',revoked=False,created_at=at))
        c.execute(meta.tables['telemetry'].insert().values(id='t',device_id='d',packet_id='old-packet',observed_at=at,received_at=at,measurements=[{'name':'soil_moisture','value':12.3,'unit':'%'}],event='Preserved event'))
        c.execute(meta.tables['chat_messages'].insert().values(id='m',project_id='p',user_id='u',question='Prior question',answer='Prior saved response',model='fixture',provider_id='fixture',context_version=1,sources=[],image_included=False,created_at=at))
    for attempt in range(2):
        migrate('upgrade','head')
        with e.connect() as c:
            assert c.execute(text('SELECT full_name FROM users')).scalar()=='Preserved user'
            assert c.execute(text('SELECT role FROM memberships')).scalar()=='owner'
            assert c.execute(text('SELECT answer FROM chat_messages')).scalar()=='Prior saved response'
            assert c.execute(text('SELECT event FROM telemetry')).scalar()=='Preserved event'
            assert c.execute(text('SELECT count(*) FROM sensor_readings')).scalar()==1
            assert abs(c.execute(text('SELECT value FROM sensor_readings')).scalar()-12.3)<1e-6
        if attempt==0:migrate('downgrade','25b229225e46')
    e.dispose()
print('Industrial migration data preservation: PASS; original identities/membership/chat/packet retained and reading backfilled once across downgrade/re-upgrade')
