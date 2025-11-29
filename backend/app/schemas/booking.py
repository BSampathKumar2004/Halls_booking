from pydantic import BaseModel
from datetime import date, time

class BookingBase(BaseModel):
    hall_id: int
    start_date: date
    end_date: date
    start_time: time
    end_time: time

class BookingCreate(BookingBase):
    payment_mode: str = "venue"
    pass

class BookingOut(BookingBase):
    id: int
    status: str
    total_price: float

    booked_by_name: str
    booked_by_email: str

    model_config = {"from_attributes": True}
