from alembic import op
import sqlalchemy as sa

revision = 'upgrade_booking_to_date_range'
down_revision = 'a4795ba8fc4e'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Safely add new columns
    try:
        op.add_column('bookings', sa.Column('start_date', sa.Date(), nullable=True))
    except:
        pass

    try:
        op.add_column('bookings', sa.Column('end_date', sa.Date(), nullable=True))
    except:
        pass

    try:
        op.add_column('bookings', sa.Column('start_time', sa.Time(), nullable=True))
    except:
        pass

    try:
        op.add_column('bookings', sa.Column('end_time', sa.Time(), nullable=True))
    except:
        pass

    # Remove old column if it still exists
    try:
        op.drop_column('bookings', 'booking_date')
    except:
        pass

    # Set safe default values so NOT NULL constraint will succeed
    op.execute("""
        UPDATE bookings 
        SET start_date = COALESCE(start_date, CURRENT_DATE),
            end_date = COALESCE(end_date, CURRENT_DATE),
            start_time = COALESCE(start_time, '00:00:00'),
            end_time = COALESCE(end_time, '23:59:59')
    """)

    # Now enforce NOT NULL
    op.alter_column('bookings', 'start_date', nullable=False)
    op.alter_column('bookings', 'end_date', nullable=False)
    op.alter_column('bookings', 'start_time', nullable=False)
    op.alter_column('bookings', 'end_time', nullable=False)


def downgrade() -> None:
    # Reverse this migration
    op.add_column('bookings', sa.Column('booking_date', sa.Date(), nullable=True))
    op.drop_column('bookings', 'end_time')
    op.drop_column('bookings', 'start_time')
    op.drop_column('bookings', 'end_date')
    op.drop_column('bookings', 'start_date')
