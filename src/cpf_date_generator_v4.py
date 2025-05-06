# cpf_date_generator_v2.py
from datetime import date, datetime # Ensure date is imported
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from cpf_data_saver_v2 import DataSaver

def custom_serializer(obj):
    """Custom serializer for non-serializable objects like datetime."""
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    # It's better to raise TypeError for unhandled types
    raise TypeError(f"Type {type(obj)} not serializable")

class DateGenerator(object):
    """
    Class to generate a dictionary of dates with start/end of month and age.
    Expects input dates are datetime.date objects.
    date_dict[date_key] = {
    # Ensure period_start isn't before the actual simulation start_d
    'period_start': max(period_start, start_date),
    'period_end': period_end,
    'age': age_at_period_end
}
    """
    def __init__(self, start_date, end_date, birth_date):
        self.start_date = start_date
        self.end_date = end_date
        self.birth_date = birth_date
        self.date_dict = {}

    def generate_date_dict(self):
        """
        Generates a dictionary of dates with start/end of month and age.
        Expects input dates are datetime.date objects.
        date_dict[date_key] = {
        'period_start': max(period_start, start_date),
        'period_end': period_end,
        'age': age_at_period_end
            }
        """
        # Input validation (optional but good practice)
        if not isinstance(self.start_date, date) or isinstance(self.start_date, datetime):
             raise TypeError(f"start_date must be a date object, got {type(start_date)}")
        if not isinstance(self.end_date, date) or isinstance(self.end_date, datetime):
             raise TypeError(f"end_date must be a date object, got {type(end_date)}")
        if not isinstance(self.birth_date, date) or isinstance(self.birth_date, datetime):
             raise TypeError(f"birth_date must be a date object, got {type(birth_date)}")
    
        self.date_dict = {}
        # Start from the first day of the start month
        current_date = self.start_date.replace(day=1)
    
        while current_date <= self.end_date:
            year = current_date.year
            month = current_date.month
    
            # Calculate period start and end as date objects
            period_start = date(year, month, 1) # First day of month
            last_day_of_month = monthrange(year, month)[1]
            period_end = date(year, month, last_day_of_month) # Last day of month
    
            # Comparison is now between two date objects
            if self.start_date > period_end:
                # If the simulation start date is after the end of the current month, skip
                current_date = current_date + relativedelta(months=1)
                continue
            
            # Calculate age at the end of the period
            age_at_period_end = relativedelta(period_end, self.birth_date).years
    
            date_key = period_end.strftime('%Y-%m')
            self.date_dict[date_key] = {
                # Ensure period_start isn't before the actual simulation start_date
                'period_start': max(period_start, self.start_date),
                'period_end': period_end,
                'age': age_at_period_end
            }
    
            # Move to the first day of the next month (date + relativedelta -> date)
            current_date = current_date + relativedelta(months=1)
            print(f'Procfessing Date Dictionary key = {date_key}, {age_at_period_end}')  # Debugging line to print each entry
           # self.save_file('date_dict', format='pickle')  # Save the date_dict to file after each entry
    
        return self.date_dict
    
    def save_file(self):
        """
        Save the date dictionary to file in the specified format: 'pickle' (binary), 'json', or 'shelve'.
        """
        data_saver = DataSaver()
        #serialize the date_dict to a file
        #key = custom_serializer(self.date_dict)
        data_saver.append(self.date_dict)
        data_saver.close()

    

if __name__ == "__main__":
    # Example usage
    start_date = date(2025, 4, 1)
    end_date = date(2080, 7, 31)
    birth_date = date(1974, 7, 6)
    dategen = DateGenerator(start_date, end_date, birth_date)
    date_dict = dategen.generate_date_dict()
    dategen.save_file()  # Save the date_dict to file after generation
    for date_key, period_info in date_dict.items():
        print(f"Period {date_key}: Start: {period_info['period_start']}, End: {period_info['period_end']}, Age: {period_info['age']}")