from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, date, datetime, time

from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.user import User
from app.models.admin import Admin
from app.models.hall import Hall
from app.schemas.booking import BookingCreate, BookingOut
from app.core.auth_utils import decode_token
from app.utils.razorpay_client import razorpay_client  # NEW

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# ---------------- DB SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- ROLE + USER/ADMIN RESOLUTION ----------------
def resolve_token_user(token: str, db: Session):
    payload = decode_token(token)

    email = payload["sub"]
    role = payload["role"]

    if role == "admin":
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin, "admin"

    if role == "user":
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user, "user"

    raise HTTPException(status_code=401, detail="Invalid role")


# =====================================================================
#                       PRICING CALCULATION FUNCTION
# =====================================================================
def calculate_price(hall: Hall, start_date, end_date, start_time, end_time):

    # SAME DAY — HOURLY
    if start_date == end_date:
        start_hr = start_time.hour + start_time.minute / 60
        end_hr = end_time.hour + end_time.minute / 60
        hours = end_hr - start_hr

        if hours <= 0:
            raise HTTPException(status_code=400, detail="Invalid hours")

        total = hours * hall.price_per_hour

        # Weekend pricing
        if start_date.weekday() >= 5:
            total *= hall.weekend_price_multiplier

        return round(total + hall.security_deposit, 2)

    # MULTI-DAY PRICING
    total = 0

    # Day 1 partial hours
    start_hours = 24 - (start_time.hour + start_time.minute / 60)
    total += start_hours * hall.price_per_hour

    # Full days between
    full_days = (end_date - start_date).days - 1
    if full_days > 0:
        for d in range(full_days):
            weekday = (start_date + timedelta(days=d + 1)).weekday()
            rate = hall.price_per_day
            if weekday >= 5:
                rate *= hall.weekend_price_multiplier
            total += rate

    # Last day partial hours
    end_hours = end_time.hour + end_time.minute / 60
    total += end_hours * hall.price_per_hour

    if end_date.weekday() >= 5:
        total *= hall.weekend_price_multiplier

    total += hall.security_deposit

    return round(total, 2)


# =====================================================================
#                            CREATE BOOKING
# =====================================================================
@router.post("/", response_model=dict)
def create_booking(data: BookingCreate, token: str, db: Session = Depends(get_db)):

    user, role = resolve_token_user(token, db)

    if role != "user":
        raise HTTPException(status_code=403, detail="Only users can book halls")

    hall = db.query(Hall).filter(Hall.id == data.hall_id, Hall.deleted == False).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    # Validations
    if data.end_date < data.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")

    if data.start_date == data.end_date and data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Overlap check
    conflict = db.query(Booking).filter(
        Booking.hall_id == data.hall_id,
        Booking.status == "booked",
        Booking.start_date <= data.end_date,
        Booking.end_date >= data.start_date,
        Booking.start_time <= data.end_time,
        Booking.end_time >= data.start_time,
    ).first()

    if conflict:
        raise HTTPException(status_code=400, detail="Hall already booked for this time range")

    # Calculate price
    total_price = calculate_price(
        hall,
        data.start_date,
        data.end_date,
        data.start_time,
        data.end_time
    )

    # Create booking object
    booking = Booking(
        user_id=user.id,
        hall_id=data.hall_id,
        start_date=data.start_date,
        end_date=data.end_date,
        start_time=data.start_time,
        end_time=data.end_time,  # FIXED BUG
        status="booked",
        total_price=total_price,
        payment_mode=data.payment_mode,
        payment_status="pending",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # ONLINE PAYMENT FLOW
    if data.payment_mode == "online":
        rp_order = razorpay_client.order.create({
            "amount": int(total_price * 100),
            "currency": "INR",
            "receipt": f"booking_{booking.id}"
        })

        booking.razorpay_order_id = rp_order["id"]
        db.commit()

        return {
            "message": "Proceed with online payment",
            "booking_id": booking.id,
            "total_price": total_price,
            "razorpay_order_id": rp_order["id"],
            "razorpay_key_id": razorpay_client.auth[0]
        }

    # PAY AT VENUE
    return {
        "message": "Booking created. Pay at venue.",
        "booking_id": booking.id,
        "total_price": total_price,
        "payment_status": "pending"
    }


# =====================================================================
#                        VERIFY RAZORPAY PAYMENT
# =====================================================================
@router.post("/verify-payment")
def verify_payment(
    booking_id: int,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    razorpay_signature: str,
    db: Session = Depends(get_db)
):

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Validate signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
    except Exception:
        booking.payment_status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    booking.payment_status = "success"
    booking.razorpay_payment_id = razorpay_payment_id
    booking.razorpay_signature = razorpay_signature
    db.commit()

    return {"message": "Payment verified successfully"}


# =====================================================================
#                          MY BOOKINGS
# =====================================================================
@router.get("/my", response_model=list[BookingOut])
def my_bookings(token: str, db: Session = Depends(get_db)):
    user, role = resolve_token_user(token, db)

    bookings = db.query(Booking).filter(Booking.user_id == user.id).all()

    return [
        BookingOut(
            id=b.id,
            hall_id=b.hall_id,
            start_date=b.start_date,
            end_date=b.end_date,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            total_price=b.total_price,
            booked_by_name=user.name,
            booked_by_email=user.email
        )
        for b in bookings
    ]


# =====================================================================
#                        CANCEL BOOKING
# =====================================================================
@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, token: str, db: Session = Depends(get_db)):
    user, role = resolve_token_user(token, db)

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "cancelled"
    db.commit()

    return {"message": "Booking cancelled successfully"}


# =====================================================================
#                ADMIN — HALL BOOKINGS LIST
# =====================================================================
@router.get("/admin/hall/{hall_id}", response_model=list[BookingOut])
def hall_bookings_admin(hall_id: int, token: str, db: Session = Depends(get_db)):

    user, role = resolve_token_user(token, db)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    bookings = db.query(Booking).filter(Booking.hall_id == hall_id).all()

    return [
        BookingOut(
            id=b.id,
            hall_id=b.hall_id,
            start_date=b.start_date,
            end_date=b.end_date,
            start_time=b.start_time,
            end_time=b.end_time,
            status=b.status,
            total_price=b.total_price,
            booked_by_name=b.user.name,
            booked_by_email=b.user.email
        )
        for b in bookings
    ]


# =====================================================================
#           ✔ A — AVAILABLE DATES (PER MONTH)
# =====================================================================
@router.get("/hall/{hall_id}/available-dates")
def available_dates(hall_id: int, month: str, db: Session = Depends(get_db)):

    try:
        year, month_num = map(int, month.split("-"))
        start_date = date(year, month_num, 1)
        end_date = (date(year + month_num // 12, (month_num % 12) + 1, 1)
                    - timedelta(days=1))
    except:
        raise HTTPException(status_code=400, detail="Invalid month format (YYYY-MM)")

    bookings = db.query(Booking).filter(
        Booking.hall_id == hall_id,
        Booking.status == "booked",
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).all()

    booked = set()

    for b in bookings:
        d = max(b.start_date, start_date)
        last = min(b.end_date, end_date)
        while d <= last:
            booked.add(d)
            d += timedelta(days=1)

    all_days = [start_date + timedelta(days=i)
                for i in range((end_date - start_date).days + 1)]

    available = [d.isoformat() for d in all_days if d not in booked]

    return {
        "hall_id": hall_id,
        "month": month,
        "available_dates": available
    }


# =====================================================================
#           ✔ B — AVAILABLE TIME SLOTS (PER DATE)
# =====================================================================
@router.get("/hall/{hall_id}/available-slots")
def available_slots(hall_id: int, date_str: str, db: Session = Depends(get_db)):

    try:
        target_date = date.fromisoformat(date_str)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")

    bookings = db.query(Booking).filter(
        Booking.hall_id == hall_id,
        Booking.status == "booked",
        Booking.start_date <= target_date,
        Booking.end_date >= target_date,
    ).all()

    # No bookings → full day available
    if not bookings:
        return {
            "hall_id": hall_id,
            "date": date_str,
            "available_slots": [{"start": "00:00", "end": "23:59"}]
        }

    bookings.sort(key=lambda b: b.start_time)
    slots = []

    current = time(0, 0)

    for b in bookings:
        if b.start_time > current:
            slots.append({
                "start": current.isoformat(timespec="minutes"),
                "end": b.start_time.isoformat(timespec="minutes"),
            })
        current = max(current, b.end_time)

    if current < time(23, 59):
        slots.append({
            "start": current.isoformat(timespec="minutes"),
            "end": "23:59",
        })

    return {
        "hall_id": hall_id,
        "date": date_str,
        "available_slots": slots
    }


# =====================================================================
#        ✔ D — MULTI-HALL CALENDAR (MONTH VIEW)
# =====================================================================
@router.get("/calendar")
def multi_hall_calendar(month: str, db: Session = Depends(get_db)):

    try:
        year, month_num = map(int, month.split("-"))
        start_date = date(year, month_num, 1)
        end_date = (date(year + month_num // 12, (month_num % 12) + 1, 1)
                    - timedelta(days=1))
    except:
        raise HTTPException(status_code=400, detail="Invalid month format (YYYY-MM)")

    halls = db.query(Hall).filter(Hall.deleted == False).all()
    hall_booked_map = {h.id: [] for h in halls}

    bookings = db.query(Booking).filter(
        Booking.status == "booked",
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).all()

    for b in bookings:
        d = max(b.start_date, start_date)
        last = min(b.end_date, end_date)
        while d <= last:
            hall_booked_map[b.hall_id].append(d.isoformat())
            d += timedelta(days=1)

    return {
        "month": month,
        "halls": [
            {"hall_id": hid, "booked_dates": sorted(list(set(days)))}
            for hid, days in hall_booked_map.items()
        ]
    }
