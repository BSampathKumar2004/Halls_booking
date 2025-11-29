from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from jose import jwt
import os
from PIL import Image
import io

from app.db.session import SessionLocal
from app.models.hall import Hall
from app.models.hall_image import HallImage
from app.utils.cloudinary_utils import upload_image, delete_image

router = APIRouter(prefix="/hall-images", tags=["Hall Images"])


# ---------------- DB SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- ADMIN TOKEN VALIDATION ----------------
def get_current_admin(token: str):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=[os.getenv("JWT_ALGORITHM")]
        )
        if payload.get("role") != "admin":
            raise HTTPException(status_code=401, detail="Admins only")
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# =====================================================================
#                  CONVERT ANY IMAGE TO JPEG (AUTO-CONVERT)
# =====================================================================
def convert_to_jpeg(upload_file: UploadFile) -> bytes:
    contents = upload_file.file.read()

    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    return buffer.read()


# =====================================================================
#                       UPLOAD IMAGE(S)
# =====================================================================
@router.post("/{hall_id}")
async def upload_hall_image(
    hall_id: int,
    token: str,
    files: list[UploadFile] = File(...),
    is_main: bool = Form(False),
    db: Session = Depends(get_db)
):
    get_current_admin(token)

    hall = db.query(Hall).filter(
        Hall.id == hall_id,
        Hall.deleted == False
    ).first()

    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    uploaded_images = []

    allowed_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/heic",
        "image/heif",
        "image/webp"
    }

    # If new upload should become main image → clear old main
    if is_main:
        db.query(HallImage).filter(
            HallImage.hall_id == hall_id
        ).update({"is_main": False})
        db.commit()

    for file in files:

        if file.content_type.lower() not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type {file.content_type}. Allowed: JPEG, JPG, PNG, HEIC, HEIF, WEBP"
            )

        # AUTO-CONVERT TO JPEG BEFORE UPLOAD
        jpeg_bytes = convert_to_jpeg(file)

        # Cloudinary upload (expects raw bytes)
        result = upload_image(jpeg_bytes)
        if not result:
            raise HTTPException(status_code=500, detail="Cloud upload failed")

        image_url = result["url"]
        public_id = result["public_id"]

        hall_image = HallImage(
            hall_id=hall.id,
            image_url=image_url,
            public_id=public_id,
            is_main=is_main
        )

        db.add(hall_image)
        db.commit()
        db.refresh(hall_image)

        uploaded_images.append({
            "id": hall_image.id,
            "url": hall_image.image_url,
            "public_id": hall_image.public_id,
            "is_main": hall_image.is_main
        })

    return {
        "message": "Images uploaded successfully",
        "images": uploaded_images
    }


# =====================================================================
#                       LIST IMAGES FOR A HALL
# =====================================================================
@router.get("/{hall_id}")
def list_hall_images(hall_id: int, db: Session = Depends(get_db)):
    hall = db.query(Hall).filter(
        Hall.id == hall_id,
        Hall.deleted == False
    ).first()

    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")

    images = db.query(HallImage).filter(
        HallImage.hall_id == hall_id
    ).all()

    main_img = next((img.image_url for img in images if img.is_main), None)

    return {
        "hall_id": hall_id,
        "main_image": main_img,
        "images": [
            {
                "id": img.id,
                "url": img.image_url,
                "public_id": img.public_id,
                "is_main": img.is_main
            }
            for img in images
        ]
    }


# =====================================================================
#                       DELETE IMAGE
# =====================================================================
@router.delete("/{image_id}")
def delete_hall_image(image_id: int, token: str, db: Session = Depends(get_db)):
    get_current_admin(token)

    image = db.query(HallImage).filter(
        HallImage.id == image_id
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete from Cloudinary
    delete_image(image.public_id)

    # Delete DB record
    db.delete(image)
    db.commit()

    return {"message": "Hall image deleted successfully"}
