from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, halls, hall_images, bookings, amenities
from app.api.routes.admin_panel import router as admin_panel_router


app = FastAPI(
    title="Hall Booking API",
    version="1.0.0",
    description="API for Hall Booking, Amenities, Users & Admin Management"
)

# CORS (important for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- ROUTERS REGISTER ORDER MATTERS --------
app.include_router(auth.router)
app.include_router(halls.router)
app.include_router(amenities.router)
app.include_router(hall_images.router)
app.include_router(bookings.router)
app.include_router(admin_panel_router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Backend running successfully"}
