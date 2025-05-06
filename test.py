import json
from src.cpf_data_saver_v2 import DataSaver
from datetime import datetime, date
from typing import Any, Union, List
with open('cpf_logs20250507.json', 'r') as f:
    logs = [json.loads(line) for line in f]


#convert list to dictionary
for item in logs:
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, (datetime, date)):
                item[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, list):
                item[key] = [v.strftime("%Y-%m-%d") if isinstance(v, (datetime, date)) else v for v in value]
            elif isinstance(value, str|int|float):
               # item[key] = value
                #try:
                #    item[key] = datetime.strptime(value, "%Y-%m-%d").date()
                #except ValueError:
                #    pass  # not a date-formatted string
                item[key] = value
#logs = {log['account']: log for log in logs}    


    
##save using datasaver
#ds = DataSaver(format='json')
#for log in logs:
#    ds.append(log)

DATE_FORMAT = "%Y-%m-%d"
config_path = 'cpf_logs20250507.json'
output_path = 'updatedlogs.json'

serializable_data = {}
with open(output_path, 'w') as f:
    json.dump(logs, f, default=str, indent=4)







