"""create agendas table

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-29 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    json_type = sa.JSON().with_variant(JSONB(), "postgresql")
    op.create_table(
        'agendas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), sa.ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('items', json_type, nullable=False, server_default='[]'),
        sa.Column('action_items', json_type, nullable=False, server_default='[]'),
        sa.Column('language', sa.String(), nullable=False, server_default='en'),
        sa.Column('ai_suggestion', json_type, nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('prompt_version', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agendas_id'), 'agendas', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_agendas_id'), table_name='agendas')
    op.drop_table('agendas')
