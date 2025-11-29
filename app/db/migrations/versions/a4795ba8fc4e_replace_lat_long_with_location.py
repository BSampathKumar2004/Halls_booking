"""replace lat-long with location

Revision ID: a4795ba8fc4e
Revises: dabca84132ac
Create Date: 2025-11-24 16:31:58.576854
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4795ba8fc4e'
down_revision: Union[str, Sequence[str], None] = 'dabca84132ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1️⃣ Add new location column as nullable first
    op.add_column('halls', sa.Column('location', sa.String(), nullable=True))

    # 2️⃣ Add deleted column, default false
    op.add_column('halls', sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False))

    # 3️⃣ Populate location for existing rows
    op.execute("UPDATE halls SET location = 'Unknown' WHERE location IS NULL")

    # 4️⃣ Convert to NOT NULL after updating
    op.alter_column('halls', 'location', nullable=False)

    # 5️⃣ Drop created_by foreign key and column if exists
    try:
        op.drop_constraint(op.f('halls_created_by_fkey'), 'halls', type_='foreignkey')
    except Exception:
        pass

    try:
        op.drop_column('halls', 'created_by')
    except Exception:
        pass

    # 6️⃣ Drop old columns
    try:
        op.drop_column('halls', 'longitude')
    except Exception:
        pass

    try:
        op.drop_column('halls', 'latitude')
    except Exception:
        pass


def downgrade() -> None:
    """Downgrade schema."""

    # Add back old columns
    op.add_column('halls', sa.Column('latitude', sa.DOUBLE_PRECISION(precision=53), nullable=True))
    op.add_column('halls', sa.Column('longitude', sa.DOUBLE_PRECISION(precision=53), nullable=True))
    op.add_column('halls', sa.Column('created_by', sa.INTEGER(), nullable=True))
    op.create_foreign_key(op.f('halls_created_by_fkey'), 'halls', 'admins', ['created_by'], ['id'])

    # Drop new columns
    op.drop_column('halls', 'deleted')
    op.drop_column('halls', 'location')
