import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

def upload_image(image_bytes: bytes):
    try:
        result = cloudinary.uploader.upload(
            image_bytes,
            folder="hall_images",
            resource_type="image",
            format="jpg",          # force output as JPG
            quality="90"
        )

        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }

    except Exception as e:
        print("Cloudinary upload error:", e)
        return None

def delete_image(public_id: str):
    try:
        cloudinary.uploader.destroy(public_id, invalidate=True)
        return True
    except Exception as e:
        print("Cloudinary delete error:", e)
        return False
