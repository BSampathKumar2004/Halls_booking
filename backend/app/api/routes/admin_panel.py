from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
import os

from app.db.session import SessionLocal
from app.models.user import User
from app.models.admin import Admin
from app.models.hall import Hall
from app.schemas.user import UserOut
from app.schemas.admin import AdminOut
from app.schemas.hall import HallOut

router = APIRouter(prefix="/admin-panel", tags=["Admin Panel"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_admin(token: str):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=[os.getenv("JWT_ALGORITHM")]
        )
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admins only")
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        

# ---------------- Get All Users ----------------
@router.get("/users", response_model=list[UserOut])
def get_all_users(token: str, db: Session = Depends(get_db)):
    validate_admin(token)
    return db.query(User).all()


# ---------------- Get All Admins ----------------
@router.get("/admins", response_model=list[AdminOut])
def get_all_admins(token: str, db: Session = Depends(get_db)):
    validate_admin(token)
    return db.query(Admin).all()


# ---------------- Get All Halls ----------------
@router.get("/halls", response_model=list[HallOut])
def get_all_halls(token: str, db: Session = Depends(get_db)):
    validate_admin(token)
    halls = db.query(Hall).filter(Hall.deleted == False).all()

    # attach amenities for each hall
    for hall in halls:
        hall.amenities = [a for a in hall.amenities]

    return halls
