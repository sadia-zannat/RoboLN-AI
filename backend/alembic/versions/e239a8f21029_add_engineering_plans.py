"""Versioned, per-project deterministic planning drafts.
Revision ID: e239a8f21029
Revises: ff6d85194d00
"""
from alembic import op
import sqlalchemy as sa
revision = 'e239a8f21029'
down_revision = 'ff6d85194d00'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('engineering_plans',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('project_id',sa.String(36),sa.ForeignKey('projects.id',ondelete='CASCADE'),nullable=False),
        sa.Column('author_id',sa.String(36),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('context_version',sa.Integer(),nullable=False),
        sa.Column('family',sa.String(48),nullable=False),
        sa.Column('status',sa.String(24),nullable=False),
        sa.Column('document',sa.JSON(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('project_id','revision'))
    op.create_index('ix_engineering_plans_project_id','engineering_plans',['project_id'])

def downgrade():
    op.drop_index('ix_engineering_plans_project_id',table_name='engineering_plans')
    op.drop_table('engineering_plans')
