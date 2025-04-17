# date_generator_v2.py
from datetime import datetime
from calendar import monthrange

def generate_date_dict(start_date: datetime, end_date: datetime):
    """
    Generate a dictionary of monthly periods from start_date to end_date (inclusive).
    Keys are month indices (0-based), values are datetime objects for the period end date.
    """
    date_dict = {}
    index = 0
    current_year = start_date.year
    current_month = start_date.month
    # Find end of the start_date's month
    last_day = monthrange(current_year, current_month)[1]
    period_end = datetime(current_year, current_month, last_day)
    if start_date > period_end:
        # If start_date is after the month end (unlikely), move to next month
        current_month += 1
        if current_month == 13:
            current_month = 1
            current_year += 1
        last_day = monthrange(current_year, current_month)[1]
        period_end = datetime(current_year, current_month, last_day)
    # Loop until end_date is reached or exceeded
    while period_end <= end_date:
        date_dict[index] = period_end
        index += 1
        # Advance to next month
        next_year = period_end.year
        next_month = period_end.month + 1
        if next_month == 13:
            next_month = 1
            next_year += 1
        last_day = monthrange(next_year, next_month)[1]
        period_end = datetime(next_year, next_month, last_day)
    return date_dict