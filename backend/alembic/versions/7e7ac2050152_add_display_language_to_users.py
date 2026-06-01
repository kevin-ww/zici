"""add display_language to users

Revision ID: 7e7ac2050152
Revises: 2903595ebba4
Create Date: 2026-05-30

Adds a display_language preference to each user account.
Allows students to choose whether AI explanations are shown in English or Chinese.
Defaults to 'en' so existing users are unaffected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '7e7ac2050152'
down_revision: Union[str, Sequence[str], None] = '2903595ebba4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'display_language',
            sa.Text(),
            nullable=False,
            server_default='en',
        ),
    )
    op.create_check_constraint(
        'ck_users_display_language',
        'users',
        "display_language IN ('en', 'zh')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_users_display_language', 'users', type_='check')
    op.drop_column('users', 'display_language')
