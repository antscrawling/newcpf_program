from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint

START_DATE = datetime(2025, 4, 1)
BIRTH_DATE = datetime(1974, 7, 6)
END_DATE = BIRTH_DATE + relativedelta(years=70)

# Total number of months from START_DATE to END_DATE
total_months = (END_DATE.year - START_DATE.year) * 12 + ((END_DATE.month - START_DATE.month) +1)

# Correct age calculation based on whether birthday has passed in that month
dates = [
    f"{(date := START_DATE + relativedelta(months=i)).strftime('%b-%Y')}, Age: {(date.year - BIRTH_DATE.year - (1 if date.month < BIRTH_DATE.month  else 0))}"
    for i in range(total_months)
]

pprint(dates)