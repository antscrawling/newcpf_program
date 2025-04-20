import calendar
import re
# Use only date from datetime
from datetime import datetime, date
from difflib import get_close_matches
# dateutil.parser returns datetime, we'll convert its output
from dateutil import parser


class MyDateTime:
    def __init__(self, mydate: str | date): # Accept string or date object
        self.mydate = mydate
        self.months = {m: i for i, m in enumerate(calendar.month_name) if m}
        self.months_abbr = {m: i for i, m in enumerate(calendar.month_abbr) if m}
        self.months_num = {str(i): i for i in range(1, 13)}

    def check_string(self):
        """Checks if the input date is a string."""
        return isinstance(self.mydate, str)

    def check_date(self): # Renamed from check_datetime
        """Checks if the input date is a date object."""
        return isinstance(self.mydate, date)

    def check_leap_year(self, year: int) -> bool:
        """Checks if a given year is a leap year."""
        return calendar.isleap(year) # Use calendar.isleap for simplicity

    def correct_month_name(self, month_str: str) -> str:
        """Attempts to correct a misspelled month using fuzzy matching."""
        month_str = month_str.capitalize()
        all_months = list(self.months.keys()) + list(self.months_abbr.keys())
        closest_match = get_close_matches(month_str, all_months, n=1, cutoff=0.7)
        return closest_match[0] if closest_match else None

    def parse_date(self, date_str: str) -> date | None: # Return date or None
        """Parses the date string using multiple formats, returning a date object."""
        # Add more formats as needed, especially common ones
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y",
            "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", # Month names
            "%Y/%m/%d", "%Y %m %d",
            # Add formats with 2-digit year if necessary, but be cautious
            # "%m/%d/%y", "%d/%m/%y", ...
        ]

        for fmt in formats:
            try:
                # Use datetime.strptime and convert to date
                dt_obj = datetime.strptime(date_str, fmt)
                return dt_obj.date()
            except ValueError:
                continue

        # Fallback to dateutil.parser, convert its result to date
        try:
            # Handle potential default times added by parser if only date is given
            dt_obj = parser.parse(date_str)
            return dt_obj.date()
        except (ValueError, TypeError): # Catch potential errors from parser
             return None


    def detect_month(self, month_input: str) -> int | None: # Return int or None
        """Detects the month (as an integer 1-12) in a date string component."""
        month_input = month_input.strip().capitalize()
        if month_input.isdigit():
            month_num = int(month_input)
            return month_num if 1 <= month_num <= 12 else None

        # Check full month names
        if month_input in self.months:
            return self.months[month_input]

        # Check abbreviated month names
        if month_input in self.months_abbr:
            return self.months_abbr[month_input]

        # Try fuzzy matching as a last resort
        corrected_month_name = self.correct_month_name(month_input)
        if corrected_month_name:
             return self.months.get(corrected_month_name) or self.months_abbr.get(corrected_month_name)

        return None

    def detect_day(self, day_input: str, month: int, year: int) -> int | None: # Return int or None
        """Validates and returns the day as an integer, adjusted for month/year."""
        try:
            day = int(day_input.strip().rstrip(',')) # Clean up input
            if day < 1:
                 return None # Day cannot be less than 1

            # Get the number of days in the given month and year
            _, max_days = calendar.monthrange(year, month)

            return day if day <= max_days else max_days # Return valid day or max day for month
        except (ValueError, TypeError):
            return None # Invalid day input

    def convert_date(self) -> date: # Return type is now date
        """Validates and converts the input to a date object."""
        if self.check_date():
            # Input is already a date object
            return self.mydate

        if not self.check_string():
             raise TypeError(f"Input must be a string or date object, got {type(self.mydate)}")

        # Attempt direct parsing first
        parsed_date = self.parse_date(self.mydate)
        if parsed_date:
            return parsed_date

        # If direct parsing fails, attempt manual parsing (more robust)
        # Normalize separators and split
        date_str_norm = re.sub(r"[\s,/.-]+", " ", self.mydate.strip())
        parts = date_str_norm.split()

        if len(parts) == 3:
            p1, p2, p3 = parts
            year, month, day = None, None, None

            try:
                # Try Y M D format (e.g., 2023 Jan 15)
                if p1.isdigit() and len(p1) == 4 and not p2.isdigit() and p3.isdigit():
                    year = int(p1)
                    month = self.detect_month(p2)
                    if month: day = self.detect_day(p3, month, year)
                # Try D M Y format (e.g., 15 Jan 2023, 15 January 2023)
                elif p1.isdigit() and not p2.isdigit() and p3.isdigit() and len(p3) == 4:
                    year = int(p3)
                    month = self.detect_month(p2)
                    if month: day = self.detect_day(p1, month, year)
                # Try M D Y format (e.g., Jan 15 2023, January 15, 2023)
                elif not p1.isdigit() and p2.isdigit() and p3.isdigit() and len(p3) == 4:
                     year = int(p3)
                     month = self.detect_month(p1)
                     if month: day = self.detect_day(p2, month, year)

                # Add other potential orders if needed (e.g., Y D M)

                if year is not None and month is not None and day is not None:
                    return date(year, month, day)

            except (ValueError, TypeError, IndexError):
                 # Errors during manual parsing attempt, fall through
                 pass

        # If all parsing attempts fail, raise an error
        raise ValueError(f"Could not parse date from input: {self.mydate}")


if __name__ == "__main__":
    # Example dates for testing
    dates = [
        '2025-04-01', '2055-07-31', '1974-07-06', date(2023, 10, 5), # Added date object
        "31/12/1999", "20291224", "decyembre 6, 1974", "Januari 15, 2023",
        "Feberuary 28, 2023", "Octuber 29, 2025", "Decembruary 25, 1999", "6/7/1974",
        "6-7-1974", "6 7 1974", "JULY 6, 1974",
        "July 6, 1974", "6-July-1974", "October 29, 2025", "October 25 2029",
        "Feb 29, 2023", # Invalid leap day
        "Feb 29, 2024", # Valid leap day
        "April 31, 2023", # Invalid day
        "Nov 30, 2024", # Valid day
        "Jan 15, 2023",
        "December 25, 99", # Ambiguous year, might fail or parse as 0099 depending on parser
        "12/31/1999", "31/12/1999", "06-July-1974", "15-Januari-2023",
        "30-Feberuary-2024", "29-Octuber-2025", "25-Decembruary-1999", "06 01 2025",
        "01-Jan-2009", "invalid-date-string" # Added invalid string
    ]

    for d in dates:
        try:
            # Create instance with the test date/string
            my_date_obj = MyDateTime(d)
            # Call convert_date to get the date object
            result = my_date_obj.convert_date()
            # Print results, using f-string debugging for clarity
            print(f"Input: {d!r:<25} | Converted: {result!s:<12} | Type: {type(result)}")

        except Exception as e:
            print(f"Input: {d!r:<25} | Error: {e}")
