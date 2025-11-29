from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.orm import relationship
from app.db.session import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    capacity = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    location = Column(String, nullable=False)

    # Pricing fields
    price_per_hour = Column(Float, nullable=False, default=0.0)
    price_per_day = Column(Float, nullable=False, default=0.0)
    weekend_price_multiplier = Column(Float, nullable=False, default=1.0)
    security_deposit = Column(Float, nullable=False, default=0.0)

    deleted = Column(Boolean, default=False)

    # Relationships
    amenities = relationship(
        "Amenity",
        secondary="hall_amenities",
        back_populates="halls"
    )

    images = relationship("HallImage", back_populates="hall", cascade="all, delete")
    bookings = relationship("Booking", back_populates="hall")
