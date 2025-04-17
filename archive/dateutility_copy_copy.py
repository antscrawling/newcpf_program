from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint
from collections import OrderedDict

class MyDateDictGenerator:
    def __init__(self, start_date=None, birth_date=None, end_date=None):
        self.start_date = start_date
        self.birth_date = birth_date
        self.end_date = end_date

    def get_date_dict(self, start_date=None, birth_date=None, end_date=None) -> dict:
        '''
        Returns a dictionary of the form:
        {
            'Apr-2025': {'age': 50},
            'May-2025': {'age': 50},
            ...
        }
        '''
        start_date = self.start_date or start_date or datetime(2025, 4, 1)
        birth_date = self.birth_date or birth_date or datetime(1974, 7, 6)
        end_date = self.end_date or end_date or (birth_date + relativedelta(years=70))

        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1

        date_dict = OrderedDict(
            ( (date := start_date + relativedelta(months=i)).strftime('%b-%Y'),
                {
                    "age": date.year - birth_date.year - (
                        1 if (date.month < birth_date.month or
                        (date.month == birth_date.month and date.day < birth_date.day)) else 0)
                }
            )
    for i in range(total_months)
)
        
        
        return date_dict

if __name__ == "__main__":
    obj = MyDateDictGenerator()
    result = obj.get_date_dict(start_date=datetime(2025, 4, 1),
                               birth_date=datetime(1974, 7, 6),
                               end_date=datetime(2044, 7, 6))
    pprint(result)