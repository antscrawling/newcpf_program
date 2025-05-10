from datetime import datetime


date_key = ''

date_keys = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12']

date_key_date_format = '%Y-%m-%d'


# FROM 'YYYY-MM'  and return as string 'YYYY-MM-DD' format
def convert_date_key_to_date(date_key):
    if date_key == '':
        return ''
    else:
        return date_key + '-01'

def custom_serializer(obj):
    """called every month to save the log"""
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")  # Convert datetime to string
    raise TypeError("Type not serializable")

for key in date_keys:
    date_key = key
    print(f"date_key: {date_key}")
    date_key = custom_serializer(datetime.strptime(date_key,'%Y-%m')) 
    print(f"date_key: {date_key}")

   
   




