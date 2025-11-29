from sqlalchemy import Column, Integer, String, Date, Time, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    hall_id = Column(Integer, ForeignKey("halls.id"))

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    status = Column(String, default="booked")
    total_price = Column(Float, nullable=False)

    # NEW PAYMENT FIELDS
    payment_mode = Column(String, default="venue")  # online | venue
    payment_status = Column(String, default="pending")  # pending, success, failed

    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)

    user = relationship("User")
    hall = relationship("Hall")
