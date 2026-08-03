"""add course status and chat_history feedback

Revision ID: 691d781a618d
Revises: 
Create Date: 2026-07-31 13:55:19.469929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '691d781a618d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Note: the autogenerate diff also proposed an unrelated
    # `ALTER COLUMN users.password_hash SET NOT NULL` -- a SQLite reflection
    # quirk, not an actual model change -- intentionally dropped from this
    # migration to keep it scoped to course status + chat feedback only.
    op.add_column('chat_history', sa.Column('feedback', sa.String(), nullable=True))
    op.add_column(
        'courses',
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('courses', 'status')
    op.drop_column('chat_history', 'feedback')
