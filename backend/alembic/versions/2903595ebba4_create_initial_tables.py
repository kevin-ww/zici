"""create initial tables

Revision ID: 2903595ebba4
Revises:
Create Date: 2026-05-30

Creates all six core tables for the Zici vocabulary learning app:
  users, words, user_progress, review_events, quiz_attempts, quiz_answers
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '2903595ebba4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('display_name', sa.Text(), nullable=True),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'words',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('word', sa.Text(), nullable=False),
        sa.Column('pinyin', sa.Text(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('char', 'word', 'idiom')", name='ck_words_type'),
    )

    op.create_table(
        'user_progress',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('word_id', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='new'),
        sa.Column('wrong_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reviewed', sa.Date(), nullable=True),
        sa.Column('next_review', sa.Date(), nullable=True),
        sa.Column('ease_factor', sa.Numeric(), nullable=False, server_default='2.5'),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('repetitions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['word_id'], ['words.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'word_id', name='uq_user_progress_user_word'),
        sa.CheckConstraint("status IN ('new', 'learning', 'mastered')", name='ck_user_progress_status'),
    )
    # Optimises GET /api/review/due — most frequent query
    op.create_index('ix_user_progress_due', 'user_progress', ['user_id', 'next_review'])

    op.create_table(
        'review_events',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('word_id', sa.Text(), nullable=False),
        sa.Column('correct', sa.Boolean(), nullable=False),
        sa.Column('previous_status', sa.Text(), nullable=True),
        sa.Column('next_status', sa.Text(), nullable=False),
        sa.Column('previous_interval', sa.Integer(), nullable=True),
        sa.Column('next_interval', sa.Integer(), nullable=False),
        sa.Column('previous_ease_factor', sa.Numeric(), nullable=True),
        sa.Column('next_ease_factor', sa.Numeric(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['word_id'], ['words.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_review_events_user_id', 'review_events', ['user_id'])

    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=True),
        sa.Column('semester', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_attempts_user_id', 'quiz_attempts', ['user_id'])

    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('quiz_attempt_id', sa.UUID(), nullable=False),
        sa.Column('word_id', sa.Text(), nullable=False),
        sa.Column('selected_answer', sa.Text(), nullable=False),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['quiz_attempt_id'], ['quiz_attempts.id']),
        sa.ForeignKeyConstraint(['word_id'], ['words.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_quiz_answers_quiz_attempt_id', 'quiz_answers', ['quiz_attempt_id'])


def downgrade() -> None:
    op.drop_table('quiz_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('review_events')
    op.drop_table('user_progress')
    op.drop_table('words')
    op.drop_table('users')
