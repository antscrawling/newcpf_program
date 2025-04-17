import calendar
import re
from datetime import datetime
from difflib import get_close_matches
from dateutil import parser


class MyDateTime:
    def __init__(self, mydate: str):
        self.mydate = mydate.strip()
        self.months = {m: i for i, m in enumerate(calendar.month_name) if m}
        self.months_abbr = {m: i for i, m in enumerate(calendar.month_abbr) if m}
        self.months_num = {str(i): i for i in range(1, 13)}

    def check_leap_year(self, year: int) -> bool:
        """Checks if a given year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def correct_month_name(self, month_str: str) -> str:
        """Attempts to correct a misspelled month using fuzzy matching."""
        month_str = month_str.capitalize()
        all_months = list(self.months.keys()) + list(self.months_abbr.keys())
        closest_match = get_close_matches(month_str, all_months, n=1, cutoff=0.7)
        return closest_match[0] if closest_match else None

    def parse_date(self, date_str: str) -> datetime:
        """Parses the date string using multiple formats."""
        formats = [
            "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%d %m %Y", "%m %d %Y",
            "%Y-%m-%d", "%Y-%d-%m", "%Y %m %d", "%Y %d %m"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Fallback to dateutil.parser
        try:
            return parser.parse(date_str)
        except ValueError:
            return None

    def detect_month(self, date_str: str) -> int:
        """Detects the month in a date string."""
        if date_str.isdigit():
            return self.months_num.get(date_str)

        valid_months = list(self.months.keys()) + list(self.months_abbr.keys())
        closest_match = get_close_matches(date_str.capitalize(), valid_months, n=1, cutoff=0.6)
        if closest_match:
            return self.months.get(closest_match[0]) or self.months_abbr.get(closest_match[0])

        return None

    def detect_day(self, day: str, month: int, year: int) -> int:
        """Validates and adjusts the day based on the month and year."""
        day = int(day)
        if month == 2:
            return 29 if self.check_leap_year(year) else 28
        elif month in [4, 6, 9, 11]:
            return min(day, 30)
        else:
            return min(day, 31)

    def check_date(self) -> datetime:
        """Validates and converts the input date string to a datetime object."""
        # Attempt to parse the date directly using known formats
        parsed_date = self.parse_date(self.mydate)
        if parsed_date:
            return parsed_date

        # Attempt to manually parse the date
        date_str = re.sub(r"[-/,]", " ", self.mydate)
        parts = date_str.split()

        if len(parts) == 3:
            try:
                # Determine the format based on the components
                if len(parts[0]) == 4:  # Year first
                    year, month, day = parts
                elif len(parts[2]) == 4:  # Year last
                    day, month, year = parts
                else:
                    raise ValueError("Invalid date format")

                # Detect and correct the month
                month = self.detect_month(month)
                if not month:
                    raise ValueError(f"Invalid month in date: {self.mydate}")

                # Detect and correct the day
                day = self.detect_day(day, month, int(year))

                return datetime(int(year), month, day)
            except Exception as e:
                raise ValueError(f"Failed to parse date: {self.mydate}. Error: {e}")

        # If all parsing attempts fail, raise an error
        raise ValueError(f"Invalid date format: {self.mydate}")


if __name__ == "__main__":
    # Example dates for testing
    dates = [
        "31/12/1999", "32-12-2029", "20291224", "decyembre 6, 1974", "Januari 15, 2023",
        "Feberuary 30, 2024", "Octuber 29, 2025", "Decembruary 25, 1999", "6/7/1974",
        "6-7-1974", "6/7/74", "6-7-74", "6 7 1974", "6 7 74", "JULY 6, 1974",
        "July 6, 1974", "July 6, 74", "6-July-1974", "October 29, 2025", "October 25 2029",
        "july 6, 0000", "Feb 29, 2023", "2023, Feb 29", "2023, 29 Feb", "Feb 29, 2024",
        "April 31, 2023", "Nov 31, 2024", "Jan 15, 2023", "Feb 29, 2028", "Feb 30, 2024",
        "March 32, 2025", "December 25, 99", "7/6/1974", "6-7-1974", "06-07-1974",
        "6 7 1974", "12/31/1999", "31/12/1999", "06-July-1974", "15-Januari-2023",
        "30-Feberuary-2024", "29-Octuber-2025", "25-Decembruary-1999", "06 01 2025",
        "0001-Jan-2026", "01-Jan-2009"
    ]

    for date in dates:
        try:
            result = MyDateTime(date).check_date()
            print(f"Input Date: {date} | Converted: {result}")
        except Exception as e:
            print(f"Input Date: {date} | Error: {str(e)}")