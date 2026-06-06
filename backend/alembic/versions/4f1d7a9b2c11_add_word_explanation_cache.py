"""add word explanation cache

Revision ID: 4f1d7a9b2c11
Revises: bf4f1a2c91e7
Create Date: 2026-06-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f1d7a9b2c11"
down_revision = "bf4f1a2c91e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "word_explanation_cache",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("word", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False, server_default=sa.text("'deepseek-chat'")),
        sa.Column("source", sa.String(), nullable=False, server_default=sa.text("'ai'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word", "level", "language", name="uq_word_explanation_cache_lookup"),
    )
    op.create_index(op.f("ix_word_explanation_cache_word"), "word_explanation_cache", ["word"], unique=False)
    op.create_index(op.f("ix_word_explanation_cache_level"), "word_explanation_cache", ["level"], unique=False)
    op.create_index(op.f("ix_word_explanation_cache_language"), "word_explanation_cache", ["language"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_word_explanation_cache_language"), table_name="word_explanation_cache")
    op.drop_index(op.f("ix_word_explanation_cache_level"), table_name="word_explanation_cache")
    op.drop_index(op.f("ix_word_explanation_cache_word"), table_name="word_explanation_cache")
    op.drop_table("word_explanation_cache")
