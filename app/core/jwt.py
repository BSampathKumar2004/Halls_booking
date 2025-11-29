from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


# -------- CREATE TOKEN --------
def create_access_token(data: dict, expires_delta: int | None = None):
    """Generate JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------- DECODE TOKEN --------
def decode_access_token(token: str):
    """Decode JWT and return the payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
