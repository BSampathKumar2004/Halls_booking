from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class HallImage(Base):
    __tablename__ = "hall_images"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)

    image_url = Column(String, nullable=False)
    public_id = Column(String, nullable=False)  # Cloudinary public ID (for delete)

    is_main = Column(Boolean, default=False, nullable=False)  # Mark main/cover image

    hall = relationship("Hall", back_populates="images")
