from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.session import Base

class HallAmenity(Base):
    __tablename__ = "hall_amenities"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"))
    amenity_id = Column(Integer, ForeignKey("amenities.id", ondelete="CASCADE"))

    __table_args__ = (UniqueConstraint("hall_id", "amenity_id", name="uq_hall_amenity"),)
