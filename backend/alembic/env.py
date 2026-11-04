from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.db import Base, DB_URL
from app import models
config=context.config
config.set_main_option('sqlalchemy.url', DB_URL)
target_metadata=Base.metadata

def run_migrations_offline():
    context.configure(url=DB_URL,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
def run_migrations_online():
    connectable=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
    if DB_URL.startswith('sqlite'):
        from sqlalchemy import event
        @event.listens_for(connectable, 'connect')
        def _enable_fk(dbapi_conn, _record):
            dbapi_conn.execute('PRAGMA foreign_keys=ON')
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
        with context.begin_transaction():context.run_migrations()
if context.is_offline_mode():run_migrations_offline()
else:run_migrations_online()
