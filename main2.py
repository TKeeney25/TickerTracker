import datetime
import enum
import math
from typing import Union, List

import numpy as np
import urllib3
import yfinance as yf
from bs4 import BeautifulSoup


class Info(enum.Enum):
    exchange = "exchange"
    shortName = "shortName"
    longName = "longName"
    morningstar_rating = "morningStarOverallRating"


class MajorHolders(enum.Enum):
    previous_close = 0
    ytd_return = 1
    expense_ratio = 2
    category = 3
    last_cap_gain = 4
    morningstar_rating = 5
    morningstar_risk_rating = 6
    sustainability_rating = 7


class InstitutionalHolders(enum.Enum):
    net_assets = 0
    beta = 1
    iyield = 2


class MarketWatch(enum.Enum):
    full_name = 'full_name'
    year_to_date = 'ytd'
    one_year = '1yr'
    three_year = '3yr'
    five_year = '5yr'
    ten_year = '10yr'


def getFullMarketWatchData(ticker: str) -> dict:  # .3-5 seconds (2.5 worst)
    return_dict = {MarketWatch.year_to_date: 0, MarketWatch.one_year: 0, MarketWatch.three_year: 0,
                   MarketWatch.five_year: 0, MarketWatch.ten_year: 0}
    list_thing = [MarketWatch.year_to_date, MarketWatch.one_year, MarketWatch.three_year, MarketWatch.five_year,
                  MarketWatch.ten_year]
    list_count = 0
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://www.marketwatch.com/investing/fund/' + ticker, headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/96.0.4664.110 Mobile Safari/537.36 Edg/96.0.1054.62',
        'referer': 'https://www.marketwatch.com/'
    })
    soup = BeautifulSoup(r.data, 'lxml')
    return_dict[MarketWatch.full_name] = soup.find_all('h1')[0].text
    for x in soup.find_all('td'):
        if x.has_attr('data-fund-return'):
            if 'N/A' in x.text:
                return_dict[list_thing[list_count]] = x.text
            else:
                return_dict[list_thing[list_count]] = float(x.text.strip('%'))
            list_count += 1
    return return_dict


def getYFinanceInfo(ticker_data: yf.Ticker) -> dict:  # 4.3 seconds
    return_dict = {}
    info = ticker_data.info
    print("Info" + str(info))
    return_dict[Info.longName] = info[Info.longName.value]
    if Info.morningstar_rating.value in info:
        return_dict[Info.morningstar_rating] = info[Info.morningstar_rating.value]
    else:
        return_dict[Info.morningstar_rating] = MyTicker.default_int
    return return_dict


def getYFinanceMajorHolders(ticker_data: yf.Ticker) -> Union[dict, bool]:  # 0.0 seconds
    # Major Holders
    #           0                   1
    #   0   Previous Close          ##.##
    #   1   YTD Return              #.##%
    #   2   Expense Ratio (net)     #.##%
    #   3   Category                string
    #   4   Last Cap Gain           #.##
    #   5   Morningstar Rating      ***** !BROKEN!
    #   6   Morningstar Risk Rating High/Med/Low
    #   7   Sustainability Rating   ###
    return_dict = {}
    major_holders = ticker_data.major_holders.get(1)
    if major_holders is None:
        return False
    if major_holders.get(MajorHolders.ytd_return.value) is None \
            or major_holders.get(MajorHolders.category.value) is None:
        return False
    return_dict[MajorHolders.ytd_return] = float(str(major_holders.get(MajorHolders.ytd_return.value)).strip('%'))
    return_dict[MajorHolders.category] = major_holders.get(MajorHolders.category.value)
    return return_dict


def getYFinanceInstitutionalHolders(ticker_data: yf.Ticker) -> dict:  # 0.0 seconds
    # Institutional
    #           0                   1
    #   0   Net Assets              #.##B
    #   1   Beta (5Y Monthly)       #.##
    #   2   Yield                   #.##%
    return_dict = {}
    institutional = ticker_data.institutional_holders.get(1)
    return_dict[InstitutionalHolders.iyield] = institutional.get(InstitutionalHolders.iyield.value)
    return return_dict


def getYFinanceNegativeYear(ticker_data: yf.Ticker) -> list:  # 0.35 seconds
    # [Method Success, result if success else year]
    hist = ticker_data.history(period="max")
    current_year = datetime.date.today().year
    compare_year = current_year - 10
    return_list = [True, False]
    while compare_year < current_year:
        try:
            year_history = hist.loc[str(compare_year) + '-01-01':str(compare_year) + '-12-31']
            if year_history.iloc[-1]['Close'] - year_history.iloc[0]['Close'] < 0 and return_list[0]:
                return [True, True]
            elif not return_list[0]:
                return [False, 10 + compare_year]
            compare_year += 1
        except IndexError:
            print("Year " + str(compare_year) + " does not exist!")
            return_list = [False, 10 + compare_year]
        finally:
            compare_year += 1
    return return_list


def getYFinanceFourWeeks(ticker_data: yf.ticker) -> float:  # 0.3 seconds
    hist = ticker_data.history(period="3mo")
    indexer = 0
    while (hist.index[-1] - hist.index[indexer]) / np.timedelta64(1, 'M') > 1:
        indexer += 1
    return ((hist.iloc[-1]['Close'] - hist.iloc[indexer]['Close']) / hist.iloc[indexer]['Close']) * 100


class MyTicker:  # 0.0 seconds
    default_string = ''
    default_float = float('-inf')
    default_int = -1

    def __init__(self, symbol: str):
        self.my_ticker: yf.Ticker = yf.Ticker(symbol)
        self.symbol: str = symbol
        self.full_name: str = self.default_string
        self.category: str = self.default_string
        self.year_to_date: float = self.default_float
        self.four_week: float = self.default_float
        self.one_year: float = self.default_float
        self.three_year: float = self.default_float
        self.five_year: float = self.default_float
        self.ten_year: float = self.default_float
        self.my_yield: float = self.default_float
        self.rating: int = self.default_int
        self.negative_year: bool = False

    def toCSV(self) -> []:
        return [self.symbol, self.full_name, self.category, self.year_to_date, self.four_week, self.one_year,
                self.three_year, self.five_year, self.ten_year, self.my_yield, self.rating, self.negative_year]

    def __str__(self):
        return 'Symbol: %s, Full Name: %s, Category: %s, YTD: %s, 4-Week: %s, 1-Year: %s, 3-Year: %s, 5-Year: %s,' \
               ' 10-Year: %s, Yield: %s, Morningstar Rating: %s, Negative Year: %s' \
               % (self.symbol, self.full_name, self.category, str(self.year_to_date), str(self.four_week),
                  str(self.one_year), str(self.three_year), str(self.five_year), str(self.ten_year), str(self.my_yield),
                  str(self.rating), str(self.negative_year))


def passesFilter(ticker_obj: MyTicker) -> bool:
    print(ticker_obj)
    if ticker_obj.one_year != ticker_obj.default_float and ticker_obj.one_year <= 0:
        return False
    if ticker_obj.three_year != ticker_obj.default_float and ticker_obj.three_year <= 0:
        return False
    if ticker_obj.five_year != ticker_obj.default_float and ticker_obj.five_year <= 0:
        return False
    if ticker_obj.ten_year != ticker_obj.default_float and ticker_obj.ten_year <= 0:
        return False
    if ticker_obj.rating != ticker_obj.default_int and ticker_obj.rating < 4:
        return False
    return True


def hasMissingData(ticker_obj: MyTicker) -> bool:
    if 'N/A' in str(ticker_obj.one_year):
        return True
    if 'N/A' in str(ticker_obj.three_year):
        return True
    if 'N/A' in str(ticker_obj.five_year):
        return True
    if 'N/A' in str(ticker_obj.ten_year):
        return True
    return False


def containsDefaults(ticker_obj: MyTicker) -> bool:
    if ticker_obj.category is None or len(str(ticker_obj.category)) == 0:
        return True
    if ticker_obj.year_to_date == ticker_obj.default_float or math.isnan(ticker_obj.year_to_date):
        return True
    if ticker_obj.one_year == ticker_obj.default_float:
        return True
    if ticker_obj.three_year == ticker_obj.default_float:
        return True
    if ticker_obj.five_year == ticker_obj.default_float:
        return True
    if ticker_obj.ten_year == ticker_obj.default_float:
        return True
    if ticker_obj.rating == ticker_obj.default_int:
        return True
    return False
