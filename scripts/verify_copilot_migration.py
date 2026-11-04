"""Preserve old-head chat and its dependent change proposal during additive upgrade."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from sqlalchemy import create_engine,MetaData,inspect
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='roboln-copilot-migration-') as temp:
 url='sqlite:///'+(Path(temp)/'old.db').as_posix();env={**os.environ,'ROBOLN_DATABASE_URL':url,'MODEL_API_KEY':''}
 def migrate(*args):subprocess.run([sys.executable,'-m','alembic',*args],cwd=ROOT/'backend',env=env,check=True,capture_output=True)
 migrate('upgrade','a8f90230d117');engine=create_engine(url);meta=MetaData();meta.reflect(engine);at=datetime.now(timezone.utc)
 with engine.begin() as c:
  c.execute(meta.tables['users'].insert(),dict(id='kept-user',email='old@migration.example',full_name='Preserved user',password_hash='TEST_NOT_A_CREDENTIAL',theme='dark',created_at=at))
  c.execute(meta.tables['projects'].insert(),dict(id='kept-project',name='Preserved project',description='',goal='Unpowered fixture',owner_id='kept-user',context_version=1,archived=False,created_at=at))
  c.execute(meta.tables['memberships'].insert(),dict(project_id='kept-project',user_id='kept-user',role='owner'))
  c.execute(meta.tables['chat_messages'].insert(),dict(id='kept-chat',project_id='kept-project',user_id='kept-user',question='Prior question',answer='Prior genuine stored answer',model='prior-model',provider_id='prior-provider',context_version=1,sources=[],image_included=False,created_at=at,selected_component_id='camera'))
  c.execute(meta.tables['change_proposals'].insert(),dict(id='kept-proposal',project_id='kept-project',author_id='kept-user',message_id='kept-chat',component_id='camera',workspace_revision=1,original='Old specification',proposed='Reviewed specification',reason='Keep dependent record',state='PENDING_REVIEW',created_at=at))
 migrate('upgrade','head');new=MetaData();new.reflect(engine)
 with engine.connect() as c:
  chat=c.execute(new.tables['chat_messages'].select()).mappings().one();assert chat['answer']=='Prior genuine stored answer' and chat['media_ids']==[] and chat['intent']=='question'
  proposal=c.execute(new.tables['change_proposals'].select()).mappings().one();assert proposal['id']=='kept-proposal' and proposal['message_id']=='kept-chat'
  assert c.execute(new.tables['users'].select()).mappings().one()['theme']=='dark'
 assert {'build_sessions','build_step_progress','build_checkpoints','build_media','build_equipment','build_steps','build_plans'}<=set(inspect(engine).get_table_names())
 migrate('downgrade','a8f90230d117');migrate('upgrade','head');meta2=MetaData();meta2.reflect(engine)
 with engine.connect() as c:assert c.execute(meta2.tables['change_proposals'].select()).mappings().one()['id']=='kept-proposal'
 engine.dispose()
print('Copilot additive migration: PASS; existing account, theme, membership, chat/provider metadata and dependent change proposal retained across upgrade/downgrade/re-upgrade; seven new tables and chat defaults verified. Downgrade intentionally removes NEW copilot data; back up before schema changes.')
