"""add deliverers table

Revision ID: a1b2c3d4e5f6
Revises: 92797acf99ff
Create Date: 2026-07-29 21:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deliverers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False, server_default='motorcycle'),
        sa.Column('latitude', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('longitude', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_busy', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_ping_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_deliverers_user_id'), 'deliverers', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_deliverers_user_id'), table_name='deliverers')
    op.drop_table('deliverers')
