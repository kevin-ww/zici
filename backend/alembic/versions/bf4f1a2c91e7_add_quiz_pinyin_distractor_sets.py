"""add quiz pinyin distractor sets

Revision ID: bf4f1a2c91e7
Revises: 7e7ac2050152
Create Date: 2026-06-05

Stores cached pinyin distractors so quizzes can reuse hard-to-distinguish
options instead of generating them from scratch on every request.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'bf4f1a2c91e7'
down_revision: Union[str, Sequence[str], None] = '7e7ac2050152'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quiz_pinyin_distractor_sets',
        sa.Column('word_id', sa.Text(), nullable=False),
        sa.Column('correct_pinyin', sa.Text(), nullable=False),
        sa.Column('distractors_json', sa.JSON(), nullable=False),
        sa.Column('difficulty_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('generation_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source', sa.Text(), nullable=False, server_default='rules'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['word_id'], ['words.id']),
        sa.PrimaryKeyConstraint('word_id'),
    )
    op.create_index(
        'ix_quiz_pinyin_distractor_sets_generation_version',
        'quiz_pinyin_distractor_sets',
        ['generation_version'],
    )


def downgrade() -> None:
    op.drop_index('ix_quiz_pinyin_distractor_sets_generation_version', table_name='quiz_pinyin_distractor_sets')
    op.drop_table('quiz_pinyin_distractor_sets')
