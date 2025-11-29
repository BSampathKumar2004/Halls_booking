from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # FIXED relationship
    halls = relationship(
        "Hall",
        secondary="hall_amenities",
        back_populates="amenities"
    )
