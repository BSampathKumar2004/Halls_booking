from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.amenities import Amenity
from app.models.hall_amenities import HallAmenity
from app.models.hall import Hall
from app.schemas.amenities import AmenityCreate, AmenityOut

from app.core.auth_utils import decode_token   # <-- Unified decoder

router = APIRouter(prefix="/amenities", tags=["Amenities"])


# ---------------- DB SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- VALIDATE ADMIN ----------------
def require_admin(token: str):
    payload = decode_token(token)      # <-- Shared decode
    role = payload.get("role")

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    return payload["sub"]


# =====================================================================
#                           CREATE AMENITY
# =====================================================================
@router.post("/", response_model=AmenityOut)
def create_amenity(
    data: AmenityCreate,
    token: str,
    db: Session = Depends(get_db)
):
    require_admin(token)

    existing = db.query(Amenity).filter(Amenity.name.ilike(data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Amenity already exists")

    amenity = Amenity(name=data.name)
    db.add(amenity)
    db.commit()
    db.refresh(amenity)

    return amenity


# =====================================================================
#                   ASSIGN AMENITIES TO A HALL
# =====================================================================
@router.post("/assign/{hall_id}")
def assign_amenities(
    hall_id: int,
    amenity_ids: list[int],
    token: str,
    db: Session = Depends(get_db)
):
    require_admin(token)

    hall = db.query(Hall).filter(Hall.id == hall_id, Hall.deleted == False).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    for amenity_id in amenity_ids:

        amenity_exists = db.query(Amenity).filter(Amenity.id == amenity_id).first()
        if not amenity_exists:
            raise HTTPException(status_code=404, detail=f"Amenity ID {amenity_id} not found")

        already_assigned = db.query(HallAmenity).filter(
            HallAmenity.hall_id == hall_id,
            HallAmenity.amenity_id == amenity_id
        ).first()

        if not already_assigned:
            db.add(HallAmenity(hall_id=hall_id, amenity_id=amenity_id))

    db.commit()

    return {"message": "Amenities assigned successfully"}


# =====================================================================
#                           LIST ALL AMENITIES
# =====================================================================
@router.get("/", response_model=list[AmenityOut])
def list_amenities(db: Session = Depends(get_db)):
    return db.query(Amenity).all()


# =====================================================================
#                     GET AMENITIES FOR A SPECIFIC HALL
# =====================================================================
@router.get("/hall/{hall_id}", response_model=list[AmenityOut])
def hall_amenities(hall_id: int, db: Session = Depends(get_db)):

    hall = db.query(Hall).filter(Hall.id == hall_id, Hall.deleted == False).first()
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    return (
        db.query(Amenity)
        .join(HallAmenity, Amenity.id == HallAmenity.amenity_id)
        .filter(HallAmenity.hall_id == hall_id)
        .all()
    )
