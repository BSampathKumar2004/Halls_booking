"""add payment fields to bookings

Revision ID: 537566340360
Revises: ac27535d3af4
Create Date: 2025-11-27 14:02:19.163293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '537566340360'
down_revision: Union[str, Sequence[str], None] = 'ac27535d3af4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('bookings', sa.Column('payment_mode', sa.String(), nullable=True))
    op.add_column('bookings', sa.Column('payment_status', sa.String(), nullable=True))
    op.add_column('bookings', sa.Column('razorpay_order_id', sa.String(), nullable=True))
    op.add_column('bookings', sa.Column('razorpay_payment_id', sa.String(), nullable=True))
    op.add_column('bookings', sa.Column('razorpay_signature', sa.String(), nullable=True))

def downgrade():
    op.drop_column('bookings', 'payment_mode')
    op.drop_column('bookings', 'payment_status')
    op.drop_column('bookings', 'razorpay_order_id')
    op.drop_column('bookings', 'razorpay_payment_id')
    op.drop_column('bookings', 'razorpay_signature')
