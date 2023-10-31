import calendar
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime


def convert_str_to_epoch_seconds(input: str, format: str = '%Y-%m-%d') -> int:
    return calendar.timegm(time.strptime(input, format))

def get_epoch_from_s(days:int=0, months:int=0, years:int=0):
    today = datetime.today() - relativedelta(years=years, months=months, days=days)
    return int(today.timestamp())

def get_ten_years_ago():
    return datetime.today().year - 10

def unix_time():
    return int(time.time_ns() / 1000000000)
