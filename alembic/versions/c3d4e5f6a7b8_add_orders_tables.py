"""add orders and order_items tables

Revision ID: c3d4e5f6a7b8
Revises: 92797acf99ff
Create Date: 2026-07-29 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '92797acf99ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela orders
    op.create_table(
        'orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('store_id', sa.UUID(), nullable=False),
        sa.Column('deliverer_id', sa.UUID(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'PREPARING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', name='orderstatus', native_enum=False),
            nullable=False,
            server_default='pendente'
        ),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('freight_value', sa.Float(), nullable=False),
        sa.Column('delivery_address', sa.String(length=500), nullable=False),
        sa.Column('delivery_latitude', sa.Float(), nullable=False),
        sa.Column('delivery_longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['users.id']),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id']),
        sa.ForeignKeyConstraint(['deliverer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_client_id'), 'orders', ['client_id'], unique=False)
    op.create_index(op.f('ix_orders_store_id'), 'orders', ['store_id'], unique=False)
    op.create_index(op.f('ix_orders_deliverer_id'), 'orders', ['deliverer_id'], unique=False)

    # Tabela order_items
    op.create_table(
        'order_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.UUID(), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_order_items_order_id'), table_name='order_items')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_orders_deliverer_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_store_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_client_id'), table_name='orders')
    op.drop_table('orders')
