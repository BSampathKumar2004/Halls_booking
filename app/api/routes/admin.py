@router.get("/stats")
def admin_stats(token: str, db: Session = Depends(get_db)):
    user, role = resolve_token_user(token, db)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    total_halls = db.query(Hall).filter(Hall.deleted == False).count()
    total_users = db.query(User).count()
    total_bookings = db.query(Booking).count()

    today = date.today()
    today_bookings = db.query(Booking).filter(
        Booking.start_date <= today, 
        Booking.end_date >= today
    ).count()

    return {
        "total_halls": total_halls,
        "total_users": total_users,
        "total_bookings": total_bookings,
        "today_bookings": today_bookings,
    }
