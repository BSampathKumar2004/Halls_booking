from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import os

from app.models.user import User
from app.models.admin import Admin

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- PASSWORD ENCRYPTION ----------
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


# ---------- GET CURRENT USER ----------
def get_current_user(token: str, db: Session):
    """Return logged-in user object from JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ---------- GET CURRENT ADMIN ----------
def get_current_admin(token: str, db: Session):
    """Return logged-in admin object from JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=401, detail="Admin access only")

        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
