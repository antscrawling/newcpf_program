# cpf_date_generator_v2.py
from datetime import date, datetime # Ensure date is imported
from dateutil.relativedelta import relativedelta
from calendar import monthrange

def generate_date_dict(start_date, end_date, birth_date):
    """
    Generates a dictionary of dates with start/end of month and age.
    Expects input dates are datetime.date objects.
    date_dict[date_key] = {
    # Ensure period_start isn't before the actual simulation start_d
    'period_start': max(period_start, start_date),
    'period_end': period_end,
    'age': age_at_period_end
}
    """
    # Input validation (optional but good practice)
    if not isinstance(start_date, date) or isinstance(start_date, datetime):
         raise TypeError(f"start_date must be a date object, got {type(start_date)}")
    if not isinstance(end_date, date) or isinstance(end_date, datetime):
         raise TypeError(f"end_date must be a date object, got {type(end_date)}")
    if not isinstance(birth_date, date) or isinstance(birth_date, datetime):
         raise TypeError(f"birth_date must be a date object, got {type(birth_date)}")

    date_dict = {}
    # Start from the first day of the start month
    current_date = start_date.replace(day=1)

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month

        # Calculate period start and end as date objects
        period_start = date(year, month, 1) # First day of month
        last_day_of_month = monthrange(year, month)[1]
        period_end = date(year, month, last_day_of_month) # Last day of month

        # Comparison is now between two date objects
        if start_date > period_end:
            # If the simulation start date is after the end of the current month, skip
            current_date = current_date + relativedelta(months=1)
            continue

        # Calculate age at the end of the period
        age_at_period_end = relativedelta(period_end, birth_date).years

        date_key = period_end.strftime('%Y-%m')
        date_dict[date_key] = {
            # Ensure period_start isn't before the actual simulation start_date
            'period_start': max(period_start, start_date),
            'period_end': period_end,
            'age': age_at_period_end
        }

        # Move to the first day of the next month (date + relativedelta -> date)
        current_date = current_date + relativedelta(months=1)

    return date_dict

if __name__ == "__main__":
    # Example usage
    start_date = date(2025, 4, 1)
    end_date = date(2080, 7, 31)
    birth_date = date(1974, 7, 6)
    
    date_dict = generate_date_dict(start_date, end_date, birth_date)
    for date_key, period_info in date_dict.items():
        print(f"Period {date_key}: Start: {period_info['period_start']}, End: {period_info['period_end']}, Age: {period_info['age']}")