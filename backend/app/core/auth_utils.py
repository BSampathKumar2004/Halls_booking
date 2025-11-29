from jose import jwt, JWTError
from fastapi import HTTPException
import os

def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=[os.getenv("JWT_ALGORITHM")]
        )

        if "sub" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
