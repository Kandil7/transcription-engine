"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='ar'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('enable_translation', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('enable_summary', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('enable_voice_analytics', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('target_language', sa.String(length=10), nullable=True),
        sa.Column('summary_length', sa.String(length=20), nullable=True),
        sa.Column('text_sample', sa.Text(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('translation', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('hierarchical_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('voice_analytics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('subtitles_srt', sa.Text(), nullable=True),
        sa.Column('subtitles_vtt', sa.Text(), nullable=True),
        sa.Column('audio_summary_url', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_profile', sa.String(length=20), nullable=True),
        sa.Column('gpu_used', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_language', 'jobs', ['language'])
    op.create_index('idx_jobs_created_at', 'jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_jobs_created_at', table_name='jobs')
    op.drop_index('idx_jobs_language', table_name='jobs')
    op.drop_index('idx_jobs_status', table_name='jobs')
    op.drop_table('jobs')
