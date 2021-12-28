import enum

from api_caller import screen, ScreenTypes

MAX_CALL_SIZE = 50


class ScreenerEnum(enum.Enum):
    finance = 'finance'
    result = 'result'
    fields = 'fields'
    total = 'total'
    quotes = 'quotes'
    symbol = 'symbol'


def getAllFunds() -> []:
    return_list = []
    for screen_type in ScreenTypes:
        offset = 0
        total_funds = MAX_CALL_SIZE * 2 + 1
        while offset < total_funds - MAX_CALL_SIZE:
            my_json = (screen(offset, MAX_CALL_SIZE, screen_type.value)
                       [ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
            total_funds = my_json[ScreenerEnum.total.value]
            for quote in my_json[ScreenerEnum.quotes.value]:
                return_list.append(quote[ScreenerEnum.symbol.value])
            offset += MAX_CALL_SIZE
    return return_list
