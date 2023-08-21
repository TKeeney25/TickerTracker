import calendar
import time

def convert_str_to_epoch_seconds(input: str, format: str = '%Y-%m-%d') -> int:
    return calendar.timegm(time.strptime(input, format))