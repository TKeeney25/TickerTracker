import enum
import json
from typing import Union

import requests
from requests import Response

import settings

YH_MAX_CALLS: int = 350
yh_total_calls: int = 0
MS_MAX_CALLS: int = 200
ms_total_calls: int = 0

yh_headers = {
    'content-type': "application/json",
    'x-rapidapi-host': "yh-finance.p.rapidapi.com",
    'x-rapidapi-key': settings.GetAPIKey()
}

ms_headers = {
    'x-rapidapi-host': "ms-finance.p.rapidapi.com",
    'x-rapidapi-key': settings.GetAPIKey()
}


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
    if ms_total_calls >= YH_MAX_CALLS:
        settings.AddToLog('checkIfCallMS()', '', settings.LogTypes.debug, str(ms_total_calls) + '/' + str(MS_MAX_CALLS))
        return False
    return True


class ScreenTypes(enum.Enum):
    etf = 'ETF'
    mutual_fund = 'MUTUALFUND'


def screen(offset: int, size: int, screen_type: ScreenTypes) -> json:
    if checkIfCallYH():
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
            ]
            '''
        querystring = {"quoteType": screen_type.value, "sortField": "fundnetassets", "region": "US",
                       "offset": str(offset), "sortType": "DESC", "size": str(size)}
        response = requests.request("POST", url, data=screener_payload, headers=yh_headers, params=querystring)
        print(response)
        return json.loads(response.text)
    else:
        return None


def getFundInfo(symbol: str) -> Union[Response, None]:
    if checkIfCallYH():
        url = "https://yh-finance.p.rapidapi.com/stock/v2/get-summary"
        querystring = {"symbol": symbol, "region": "US"}
        response = requests.request("GET", url, headers=yh_headers, params=querystring)
        print(response)
        return response
    else:
        return None


def getPerformanceID(symbol: str) -> Union[str, None]:
    if checkIfCallMS():
        url = "https://ms-finance.p.rapidapi.com/market/v2/auto-complete"
        querystring = {"q": symbol}
        response = requests.request("GET", url, headers=ms_headers, params=querystring)
        print(response)
        return json.loads(response.text)['results'][0]['performanceId']
    else:
        return None


def getMorningstarRating(symbol: str) -> Union[int, None]:
    url = "https://ms-finance.p.rapidapi.com/stock/get-detail"
    querystring = {"PerformanceId": getPerformanceID(symbol)}
    if checkIfCallMS():
        response = requests.request("GET", url, headers=ms_headers, params=querystring)
        print(response)
        return json.loads(response.text)[0]['Detail']['StarRating']
    else:
        return None
