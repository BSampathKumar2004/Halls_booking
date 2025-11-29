from pydantic import BaseModel
from typing import List, Optional
from app.schemas.amenities import AmenityOut


class HallBase(BaseModel):
    name: str
    description: str
    capacity: int
    address: str
    location: str

    # Pricing fields
    price_per_hour: float
    price_per_day: float
    weekend_price_multiplier: float = 1.0
    security_deposit: float = 0.0


class HallCreate(HallBase):
    amenity_ids: Optional[List[int]] = []


class HallOut(HallBase):
    id: int
    amenities: List[AmenityOut] = []

    model_config = {
        "from_attributes": True
    }
