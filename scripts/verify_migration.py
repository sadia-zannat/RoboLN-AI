"""Real isolated Alembic roundtrip, including actual schema state checks."""
import os,subprocess,sys,tempfile,pathlib
from sqlalchemy import create_engine,inspect,text
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='roboln-v2-migration-') as tmp:
  db=pathlib.Path(tmp)/'fresh.sqlite'
  env={**os.environ,'ROBOLN_DATABASE_URL':'sqlite:///'+str(db)}
  def run(*args):subprocess.run([sys.executable,'-m','alembic',*args],cwd=root/'backend',env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  engine=create_engine(env['ROBOLN_DATABASE_URL'])
  run('upgrade','e239a8f21029')
  with engine.begin() as c:
    c.execute(text("INSERT INTO users(id,email,full_name,password_hash,theme,created_at) VALUES ('migration-probe','migration@example.com','Preserved identity','schema-test-only','light',CURRENT_TIMESTAMP)"))
  run('upgrade','head')
  with engine.connect() as c:assert c.execute(text("SELECT full_name FROM users WHERE id='migration-probe'")).scalar()=='Preserved identity'
  tables=inspect(engine).get_table_names()
  assert 'projects' in tables and 'login_throttles' in tables and 'engineering_plans' in tables,tables
  with engine.connect() as c:
    version=c.execute(text('select version_num from alembic_version')).scalar()
    assert version=='c17a90bd4201',version
  run('downgrade','base')
  assert inspect(engine).get_table_names()==['alembic_version'],inspect(engine).get_table_names()
  run('upgrade','head')
  assert 'telemetry' in inspect(engine).get_table_names()
  with engine.connect() as c:assert c.execute(text('select version_num from alembic_version')).scalar()==version
  engine.dispose()
print('Alembic upgrade/downgrade/upgrade: PASS; five-revision chain ending c17a90bd4201; full workbench schema')
