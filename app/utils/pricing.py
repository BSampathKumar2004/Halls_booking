from datetime import timedelta

def calculate_booking_price(hall, start_date, end_date, start_time, end_time):
    total = 0

    # Number of days
    day_count = (end_date - start_date).days + 1

    # If same day, calculate hours
    if start_date == end_date:
        hours = (
            datetime.combine(start_date, end_time) -
            datetime.combine(start_date, start_time)
        ).seconds / 3600

        total = hours * hall.price_per_hour
    else:
        # multi-day booking = daily rate
        total = day_count * hall.price_per_day

    # Weekend extra charge
    weekend_days = 0
    d = start_date
    while d <= end_date:
        if d.weekday() in (5, 6):  # Saturday-Sunday
            weekend_days += 1
        d += timedelta(days=1)

    total += weekend_days * hall.weekend_extra

    # Add security deposit
    total += hall.security_deposit

    return round(total, 2)
