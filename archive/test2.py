from datetime import datetime, timedelta
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from pprint import pprint
#from dateutility import  MyDateDictGenerator
import json
from import_config import get_the_config
from convert_date import MyDateTime





#config = get_the_config()
test_date = MyDateTime()
#globals().update({
#    k: datetime(test_date.check_date(*v)) if isinstance(v, list) and len(v) == 3 and all(isinstance(i, int) for i in v)
#    else v
#    for k, v in get_the_config().items()
#})
globals().update({
    k: datetime(test_date.check_date(*v)) if isinstance(v, list) and len(v) == 3 and all(isinstance(i, int) for i in v)
    else (", ".join(map(str, v)) if isinstance(v, list) else v)  # Convert list to string if needed
    for k, v in get_the_config().items()
})


print(globals())