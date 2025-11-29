from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.session import SessionLocal
from app.models.hall import Hall
from app.models.hall_amenities import HallAmenity
from app.models.amenities import Amenity
from app.schemas.hall import HallCreate, HallOut
from app.models.hall_image import HallImage
from app.core.auth_utils import decode_token

router = APIRouter(prefix="/halls", tags=["Halls"])


# ---------------- DB SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- ADMIN VALIDATION ----------------
def require_admin(token: str):
    payload = decode_token(token)

    if payload["role"] != "admin":
        raise HTTPException(status_code=401, detail="Admins only")

    return payload["sub"]  # returns admin email


# =====================================================================
#                           CREATE HALL
# =====================================================================
@router.post("/", response_model=HallOut)
def create_hall(data: HallCreate, token: str, db: Session = Depends(get_db)):
    require_admin(token)

    hall = Hall(
        name=data.name,
        description=data.description,
        capacity=data.capacity,
        address=data.address,
        location=data.location,

        price_per_hour=data.price_per_hour,
        price_per_day=data.price_per_day,
        weekend_price_multiplier=data.weekend_price_multiplier,
        security_deposit=data.security_deposit,

        deleted=False
    )

    db.add(hall)
    db.commit()
    db.refresh(hall)

    # Add amenities
    if data.amenity_ids:
        for aid in data.amenity_ids:
            if not db.query(Amenity).filter(Amenity.id == aid).first():
                raise HTTPException(status_code=404, detail=f"Amenity ID {aid} not found")
            db.add(HallAmenity(hall_id=hall.id, amenity_id=aid))

        db.commit()

    # Reload amenities
    hall.amenities = (
        db.query(Amenity)
        .join(HallAmenity, HallAmenity.amenity_id == Amenity.id)
        .filter(HallAmenity.hall_id == hall.id)
        .all()
    )

    return hall


# =====================================================================
#                           EDIT HALL
# =====================================================================
@router.put("/{hall_id}", response_model=HallOut)
def edit_hall(hall_id: int, data: HallCreate, token: str, db: Session = Depends(get_db)):
    require_admin(token)

    hall = db.query(Hall).filter(Hall.id == hall_id, Hall.deleted == False).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    hall.name = data.name
    hall.description = data.description
    hall.capacity = data.capacity
    hall.address = data.address
    hall.location = data.location

    hall.price_per_hour = data.price_per_hour
    hall.price_per_day = data.price_per_day
    hall.weekend_price_multiplier = data.weekend_price_multiplier
    hall.security_deposit = data.security_deposit

    db.commit()

    # Update amenities
    db.query(HallAmenity).filter(HallAmenity.hall_id == hall.id).delete()
    if data.amenity_ids:
        for aid in data.amenity_ids:
            db.add(HallAmenity(hall_id=hall.id, amenity_id=aid))
    db.commit()

    # Reload amenities
    hall.amenities = (
        db.query(Amenity)
        .join(HallAmenity, HallAmenity.amenity_id == Amenity.id)
        .filter(HallAmenity.hall_id == hall.id)
        .all()
    )

    return hall


# =====================================================================
#                       DELETE (SOFT DELETE)
# =====================================================================
@router.delete("/{hall_id}")
def delete_hall(hall_id: int, token: str, db: Session = Depends(get_db)):
    require_admin(token)

    hall = db.query(Hall).filter(Hall.id == hall_id, Hall.deleted == False).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    hall.deleted = True
    db.commit()

    return {"message": "Hall deleted successfully"}


# =====================================================================
#                           LIST HALLS
# =====================================================================
@router.get("/", response_model=list[HallOut])
def list_halls(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10,
    location: str | None = None,
    min_capacity: int | None = None,
    max_capacity: int | None = None,
):
    query = db.query(Hall).options(joinedload(Hall.amenities)).filter(Hall.deleted == False)

    if location:
        query = query.filter(Hall.location.ilike(f"%{location}%"))

    if min_capacity:
        query = query.filter(Hall.capacity >= min_capacity)

    if max_capacity:
        query = query.filter(Hall.capacity <= max_capacity)

    halls = query.offset((page - 1) * limit).limit(limit).all()

    return halls


# =====================================================================
#                           HALL DETAILS
# =====================================================================
@router.get("/{hall_id}", response_model=HallOut)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = (
        db.query(Hall)
        .filter(Hall.id == hall_id, Hall.deleted == False)
        .first()
    )

    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    images = db.query(HallImage).filter(HallImage.hall_id == hall_id).all()

    hall.images = images  # inject into HallOut serializer

    return hall

