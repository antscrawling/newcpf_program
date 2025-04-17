import json
from datetime import datetime
import calendar
import re
from difflib import get_close_matches
from dateutil import parser

class MyDateTime:
    def __init__(self):
        """Initialize month mappings for full names, abbreviations, and numeric values."""
        self.months = {m: i for i, m in enumerate(calendar.month_name) if m}
        self.months_abbr = {m: i for i, m in enumerate(calendar.month_abbr) if m}
        self.months_num = {str(i): i for i in range(1, 13)}  # Support month numbers as strings

    def check_leap_year(self, year):
        """Checks if a given year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def correct_month_name(self, month_str):
        """Attempts to correct a misspelled month using fuzzy matching."""
        month_str = month_str.capitalize()
        all_months = list(self.months.keys()) + list(self.months_abbr.keys())
        closest_match = get_close_matches(month_str, all_months, n=1, cutoff=0.7)
        return closest_match[0] if closest_match else None

    def convert_string(self, date_str):
        """Converts input date string to a normalized form."""
        if '0000' in date_str:
            date_str = date_str.replace('0000', '2000')
        return date_str.strip().title()

    def parse_date(self, date_str):
        """Parses the date string using multiple formats."""
        formats = ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%d %m %Y", "%m %d %Y", "%Y-%m-%d", "%Y-%d-%m", "%Y %m %d", "%Y %d %m"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
            
        # As a fallback, use dateutil.parser (tries multiple formats)
        try:
            return parser.parse(date_str).date()
        except ValueError:
            return None

    def check_date(self, date_str) -> str:
        """Checks if a date is valid and returns the corrected date."""
        
        parsed_date = self.parse_date(date_str)
        if parsed_date is not None:
            return parsed_date.strftime("%d-%B-%Y")
        
        # If parsing fails, attempt to correct the date manually
        date_str = re.sub(r"[-/,]", " ", date_str)
        parts = date_str.split()
        myiter = iter(parts)
        first = self.determine_length(date_str)
        
        if first == 'year':
            year = next(myiter)
            month = next(myiter)
            _, n_month = self.detect_month(month)
            day = next(myiter)
            n_day, n_month, n_year = self.detect_day(day, n_month, year)
        elif first == 'day':
            day = next(myiter)
            month = next(myiter)
            _, n_month = self.detect_month(month)
            year = next(myiter)
            n_day, n_month, n_year = self.detect_day(day, n_month, year)
        elif first == 'month':
            month = next(myiter)
            _, n_month = self.detect_month(month)
            day = next(myiter)
            year = next(myiter)
            n_day, n_month, n_year = self.detect_day(day, n_month, year)

        return datetime(n_year, n_month, n_day).strftime("%d-%B-%Y")

    def determine_length(self, date_str):
        """Determines the format of the date string based on its components."""
        mylist = date_str.split()
        for item in mylist:
            if item.isdigit() and mylist[1].isdigit() and mylist[2].isdigit():
                if int(item) > 12:
                    return 'day'
                else:
                    return 'month'
            if item.isdigit() and len(item) == 4:
                return 'year'
            elif item.isdigit() and len(item) == 2:
                return 'day'
            else:
                return 'month'

    def detect_month(self, date_str):
        """Detects the month in a date string."""
        if date_str.isdigit():
            return True, self.months_num.get(date_str)
        
        valid_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                        "January", "February", "March", "April", "May", "June", "July", "August", "September",
                        "October", "November", "December", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
                        "OCTOBER", "NOVEMBER", "DECEMBER", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        month_pattern = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:uary|ch|ril|ember|ust|e)?\b"
        match = re.search(month_pattern, date_str, re.IGNORECASE)
        if match:
            if len(match.group()) > 3:
                return True, self.months.get(match.group())
            return True, self.months_abbr.get(match.group())
        else:
            closest_match = get_close_matches(date_str, valid_months, n=1, cutoff=0.6)
            if closest_match:
                if len(closest_match[0]) > 3:
                    return True, self.months.get(closest_match[0])
                return True, self.months_abbr.get(closest_match[0])  # Return corrected month name

        return False, None  # No valid month found

    def detect_day(self, day_str, month, year):
        """Detects the day in a date string."""
        if year.isdigit() and len(year) == 2:
            n_year = int(f'20{year}')
        elif year.isdigit() and int(year) == 0:
            n_year = int(f'20{year}')
        elif year.isdigit() and int(year) < 1900:
            n_year = 1900
        elif year.isdigit() and 1900 < int(year) <= 2025:
            n_year = int(year)
        elif year.isdigit() and int(year) > datetime.now().year:
            n_year = 2025
        else:
            n_year = int(year)
           
        n_day = day_str if type(day_str) == int else int(day_str)    
        n_month = month if type(month) == int else int(month)
        leap_year = self.check_leap_year(n_year)
        if leap_year and n_month == 2:
            return 29, n_month, n_year
        
        if n_day > 28 and n_month == 2:
            return 28, n_month, n_year
        elif n_day > 30 and n_month in [4, 6, 9, 11]:    
            return 30, n_month, n_year
        elif n_day > 31 and n_month in [1, 3, 5, 7, 8, 10, 12]:
            return 31, n_month, n_year
        else:
            return (n_day if 1 <= n_day <= 31 else None), n_month, n_year

if __name__ == "__main__":
    # Example dates for testing (including misspelled months)
    dates = [
       "31/12/1999", "32-12-2029", "20291224", "decyembre 6, 1974", "Januari 15, 2023", "Feberuary 30, 2024",
       "Octuber 29, 2025", "Decembruary 25, 1999", "6/7/1974", "6-7-1974", "6/7/74", "6-7-74", "6 7 1974", "6 7 74",
       "JULY 6, 1974", "July 6, 1974", "July 6, 74", "6-July-1974", "October 29, 2025", "October 25 2029", "july 6, 0000",
       "Feb 29, 2023", "2023, Feb 29", "2023, 29 Feb", "Feb 29, 2024", "April 31, 2023", "Nov 31, 2024", "Jan 15, 2023",
       "Feb 29, 2028", "Feb 30, 2024", "March 32, 2025", "December 25, 99", "7/6/1974", "6-7-1974", "06-07-1974",
       "6 7 1974", "12/31/1999", "31/12/1999", "06-July-1974", "15-Januari-2023", "30-Feberuary-2024", "29-Octuber-2025",
       "25-Decembruary-1999", "06 01 2025", "0001-Jan-2026", "01-Jan-2009",
        "31 2 233541 ",'1 3 4', '9 0 8'
    ]

    my_date_handler = MyDateTime()

    for date in dates:
        try:
            if len(date)==3:
                print(f' my test Input Date: {date} | Converted: {date}')
            result = my_date_handler.check_date(date)
            print(f'Input Date: {date} | Converted: {result}')
        except Exception as e:
            print(f'Input Date: {date} | Error: {str(e)}')