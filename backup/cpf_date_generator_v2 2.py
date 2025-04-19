# date_generator_v2.py
from datetime import datetime
from calendar import monthrange
from convertdate import is_leapyear

def generate_date_dict(start_date: datetime, end_date: datetime, birth_date: datetime) -> dict:
    """
    Generate a dictionary of monthly periods from start_date to end_date (inclusive).
    Keys are month indices (0-based), values are dictionaries containing:
        - 'period_end': datetime object for the period end date
        - 'age': age at the end of the period
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
        # Calculate age at the end of the period
        age = period_end.year - birth_date.year - ((period_end.month, period_end.day) < (birth_date.month, birth_date.day))
        # Add the period end date and age to the dictionary
        date_dict[index] = {
            'period_end': period_end,
            'age': age
        }
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

if __name__ == "__main__":
    # Example usage
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2080, 7, 31)
    birth_date = datetime(1974, 7, 6)
    
    date_dict = generate_date_dict(start_date, end_date, birth_date)
    for index, period_info in date_dict.items():
        print(f"Period {index}: {period_info['period_end'].strftime('%Y-%m-%d')}, Age: {period_info['age']}")