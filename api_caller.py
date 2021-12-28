import enum
import json
import requests
import settings

MAX_CALLS = 10
total_calls: int = 0

headers = {
    'content-type': "application/json",
    'x-rapidapi-host': "yh-finance.p.rapidapi.com",
    'x-rapidapi-key': settings.Settings.GetAPIKey()
}


def checkIfCall() -> bool:
    global total_calls
    total_calls += 1
    print("Total API Calls: " + str(total_calls) + "/" + str(MAX_CALLS))
    if total_calls >= MAX_CALLS:
        settings.Settings.AddToLog('checkIfCall', '', 'Exceeded maximum API calls '
                                   + str(total_calls) + '/' + str(MAX_CALLS))
        return False
    return True


class ScreenTypes(enum.Enum):
    etf = 'ETF'
    mutual_fund = 'MUTUALFUND'


def screen(offset: int, size: int, screen_type: ScreenTypes) -> json:
    if checkIfCall():
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
        response = requests.request("POST", url, data=screener_payload, headers=headers, params=querystring)
        print(response)
        return json.loads(response.text)
    else:
        return None


def getFundInfo(symbol: str) -> json:
    if checkIfCall():
        url = "https://yh-finance.p.rapidapi.com/stock/v2/get-summary"
        querystring = {"symbol": symbol, "region": "US"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(response)
        return json.loads(response.text)
    else:
        return None
