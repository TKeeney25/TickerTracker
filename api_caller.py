import enum
import json
from functools import partial

import requests
from requests import Response
from time import sleep
from typing import Union, Optional, Any

import settings

# region 'Globals/Constants'

YH_MAX_CALLS: int = 40000
yh_total_calls: int = 0
MS_MAX_CALLS: int = 8000
ms_total_calls: int = 0

YH_HEADERS = {
    'content-type': "application/json",
    'x-rapidapi-host': "yh-finance.p.rapidapi.com",
    'x-rapidapi-key': settings.GetAPIKey()
}

MS_HEADERS = {
    'x-rapidapi-host': "ms-finance.p.rapidapi.com",
    'x-rapidapi-key': settings.GetAPIKey()
}
# endregion


class ScreenTypes(enum.Enum):
    etf = 'ETF'
    mutual_fund = 'MUTUALFUND'


def getFundInfo(symbol: str) -> Union[Response, None]:
    url = "https://yh-finance.p.rapidapi.com/stock/v2/get-summary"
    querystring = {"symbol": symbol, "region": "US"}
    response = requests.request("GET", url, headers=YH_HEADERS, params=querystring)
    print(response)
    return response


def checkIfCallYH() -> bool:
    global yh_total_calls
    yh_total_calls += 1
    print("Total YH API Calls: " + str(yh_total_calls) + "/" + str(YH_MAX_CALLS))
    if yh_total_calls >= YH_MAX_CALLS:
        settings.AddToLog('checkIfCallYH()', '', settings.LogTypes.debug, str(yh_total_calls) + '/' + str(YH_MAX_CALLS))
        return False
    return True


def checkIfCallMS() -> bool:
    global ms_total_calls
    ms_total_calls += 1
    print("Total MS API Calls: " + str(ms_total_calls) + "/" + str(MS_MAX_CALLS))
    if ms_total_calls >= MS_MAX_CALLS:
        settings.AddToLog('checkIfCallMS()', '', settings.LogTypes.debug, str(ms_total_calls) + '/' + str(MS_MAX_CALLS))
        return False
    return True


# region 'Screens'
def screen(offset: int, size: int, screen_type: ScreenTypes, payload='') -> json:
    url = "https://yh-finance.p.rapidapi.com/screeners/list"
    screener_payload = '''
        [
            {
                "operator":"EQ",
                "operands": [
                    "region",
                    "us"
                ]
            }
            %s
        ]
        ''' % payload
    querystring = {"quoteType": screen_type.value, "sortField": "fundnetassets", "region": "US",
                   "offset": str(offset), "sortType": "DESC", "size": str(size)}
    response = requests.request("POST", url, data=screener_payload, headers=YH_HEADERS, params=querystring)
    print(response)
    if '401' in str(response):
        settings.log('Incorrect API Key! Stopping!')
        settings.current_stage = 'Stopped'
        exit(-1)
    return json.loads(response.text)


def screenBetweenFundPrices(
        offset: int, size: int, screen_type: ScreenTypes, price_low: float, price_high: float) -> json:
    screener_payload = '''
            ,
            {
                "operator":"btwn",
                "operands": [
                    "intradayprice",
                    %.4f,
                    %.4f
                ]
            }
        ''' % (price_low, price_high)
    return doAPICall(YHFunctions.screen, offset, size, screen_type, screener_payload)


def screenGreaterThanFundPrices(offset: int, size: int, screen_type: ScreenTypes, greater_than: float) -> json:
    screener_payload = '''
            ,
            {
                "operator":"GT",
                "operands": [
                    "intradayprice",
                    %.4f
                ]
            }
        ''' % greater_than
    return doAPICall(YHFunctions.screen, offset, size, screen_type, screener_payload)


# endregion


def getMorningstarRating(symbol: str) -> Union[int, None]:
    ids = doAPICall(MSFunctions.getPerformanceIDs, symbol)
    for my_id in ids:
        result = doAPICall(MSFunctions.getRating, my_id)
        if result is not None:
            return result
    return None


def getRating(my_id: str):
    url = "https://ms-finance.p.rapidapi.com/stock/get-detail"
    querystring = {"PerformanceId": my_id}
    response = requests.request("GET", url, headers=MS_HEADERS, params=querystring)
    print(response)
    json_response = json.loads(response.text)
    if len(json_response) > 0 and \
            'Detail' in json_response[0] and 'StarRating' in json_response[0]['Detail']:
        return json_response[0]['Detail']['StarRating']
    return None


def getPerformanceIDs(symbol: str) -> Optional[list[Any]]:
    url = "https://ms-finance.p.rapidapi.com/market/v2/auto-complete"
    querystring = {"q": symbol}
    response = requests.request("GET", url, headers=MS_HEADERS, params=querystring)
    print(response)
    return_id = []
    for result in json.loads(response.text)['results']:
        return_id.append(result['performanceId'])
    return return_id


class YHFunctions(enum.Enum):
    getFundInfo = partial(getFundInfo)
    screen = partial(screen)
    screenBetweenFundPrices = partial(screenBetweenFundPrices)
    screenGreaterThanFundPrices = partial(screenGreaterThanFundPrices)

    def __call__(self, *args):
        return self.value(*args)


class MSFunctions(enum.Enum):
    getMorningstarRating = partial(getMorningstarRating)
    getPerformanceIDs = partial(getPerformanceIDs)
    getRating = partial(getRating)

    def __call__(self, *args):
        return self.value(*args)


def doAPICall(function: Union[YHFunctions, MSFunctions], *args) -> Any:
    should_call = False
    if function in YHFunctions:
        should_call = checkIfCallYH()
    elif function in MSFunctions:
        should_call = checkIfCallMS()
    print('doAPICall')
    print(should_call)
    if should_call:
        for i in range(5 * 12, 0, -1):
            try:
                return function.value(*args)
            except ConnectionError as ex:
                print("Lost Connection. %s attempts remaining" % i)
                settings.AddToLog('doYHCall(%s)' % str(function.value), str(args), settings.LogTypes.debug, ex)
                sleep(5)
    else:
        return None

