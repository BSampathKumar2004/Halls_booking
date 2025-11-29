from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.admin import AdminCreate, AdminLogin
from app.schemas.user import UserCreate, UserLogin
from app.models.admin import Admin
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token  # <-- Correct import

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------- DB SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
#                           ADMIN REGISTER
# =====================================================================
@router.post("/admin/register")
def admin_register(data: AdminCreate, db: Session = Depends(get_db)):
    if db.query(Admin).filter(Admin.email == data.email).first():
        raise HTTPException(status_code=400, detail="Admin already exists")

    hashed = hash_password(data.password)
    admin = Admin(name=data.name, email=data.email, password_hash=hashed)

    db.add(admin)
    db.commit()

    return {"message": "Admin registered successfully"}


# =====================================================================
#                           ADMIN LOGIN
# =====================================================================
@router.post("/admin/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == data.email).first()

    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": admin.email, "role": "admin"})

    return {
        "access_token": token,
        "role": "admin",
        "token_type": "bearer"
    }


# =====================================================================
#                           USER REGISTER
# =====================================================================
@router.post("/user/register")
def user_register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(data.password)
    user = User(name=data.name, email=data.email, password_hash=hashed)

    db.add(user)
    db.commit()

    return {"message": "User registered successfully"}


# =====================================================================
#                           USER LOGIN
# =====================================================================
@router.post("/user/login")
def user_login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email, "role": "user"})

    return {
        "access_token": token,
        "role": "user",
        "token_type": "bearer"
    }
