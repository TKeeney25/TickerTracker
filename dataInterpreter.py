import datetime
import enum
import threading

import numpy as np
from yfinance import ticker

import data_grab
import settings
import yfinance as yf
import csv


def getTicker(my_ticker: str, attempts=5) -> dict:
    dictionary = {}
    while attempts > 0:
        try:
            print("Ticker " + my_ticker + " pre-collection")
            ticker_data = yf.Ticker(my_ticker)
            # Info
            print(Info.longName in dictionary)
            exit(-1)
            if Info.longName not in dictionary:
                info = ticker_data.info
                dictionary[Info.longName] = info[Info.longName.value]

            # Major Holders
            #           0                   1
            #   0   Previous Close          ##.##
            #   1   YTD Return              #.##%
            #   2   Expense Ratio (net)     #.##%
            #   3   Category                string
            #   4   Last Cap Gain           #.##
            #   5   Morningstar Rating      *****
            #   6   Morningstar Risk Rating High/Med/Low
            #   7   Sustainability Rating   ###
            if MajorHolders.ytd_return not in dictionary:
                major_holders = ticker_data.major_holders.get(1)
                dictionary[MajorHolders.ytd_return] = major_holders.get(MajorHolders.ytd_return.value).strip('%')
                dictionary[MajorHolders.morningstar_rating] = len(
                    major_holders.get(MajorHolders.morningstar_rating.value))
                dictionary[MajorHolders.category] = major_holders.get(MajorHolders.category.value)

            # Institutional
            #           0                   1
            #   0   Net Assets              #.##B
            #   1   Beta (5Y Monthly)       #.##
            #   2   Yield                   #.##%
            if InstitutionalHolders.iyield not in dictionary:
                institutional = ticker_data.institutional_holders.get(1)
                dictionary[InstitutionalHolders.iyield] = institutional.get(InstitutionalHolders.iyield.value)

            if "negativeYear" not in dictionary:
                dictionary["negativeYear"] = convertBoolToChar(hasHadNegativeYear(ticker_data))
            if "four_weeks" not in dictionary:
                dictionary["four_weeks"] = get4Week(ticker_data)
            print("Ticker post-collection")
            print(dictionary)
            print(my_ticker)
            return dictionary
        except Exception as err:
            print(str(err) + " Error on ticker! " + my_ticker + "\n" + str(attempts) + " attempts remaining")
        finally:
            attempts -= 1
    return dictionary


class myThread(threading.Thread):
    def __init__(self, my_ticker):
        threading.Thread.__init__(self)
        self.my_ticker: str = my_ticker
        self.return_dict: dict = {}

    def run(self):
        print("Starting " + self.my_ticker)
        self.return_dict = getTicker(self.my_ticker)

    def join(self, timeout=None) -> dict:
        threading.Thread.join(self, timeout)
        return self.return_dict


class Info(enum.Enum):
    exchange = "exchange"
    shortName = "shortName"
    longName = "longName"


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
    year_to_date = 'ytd'
    one_year = '1yr'
    three_year = '3yr'
    five_year = '5yr'
    ten_year = '10yr'


def convertBoolToChar(boolean: bool) -> str:
    if boolean:
        return 'Y'
    return 'N'


def hasHadNegativeYear(ticker_data: ticker) -> bool:
    print("startNegative")
    hist = ticker_data.history(period="max")
    current_year = datetime.date.today().year
    print(current_year)
    compareYear = current_year - 10
    while compareYear < current_year:
        try:
            year_history = hist.loc[str(compareYear) + '-01-01':str(compareYear) + '-12-31']
            print(year_history)
            print(year_history.iloc[0]['Close'])
            print(year_history.iloc[-1]['Close'])
            if year_history.iloc[-1]['Close'] - year_history.iloc[0]['Close'] < 0:
                return True
        except IndexError:
            print("Year " + str(compareYear) + " does not exist!")
        finally:
            compareYear += 1
    return False


def get4Week(ticker_data: ticker) -> float:
    hist = ticker_data.history(period="3mo")
    indexer = 0
    while (hist.index[-1] - hist.index[indexer]) / np.timedelta64(1, 'M') > 1:
        print(hist.index[indexer])
        print(((hist.iloc[-1]['Close'] - hist.iloc[indexer]['Close']) / hist.iloc[indexer]['Close']) * 100)
        indexer += 1
    print(hist.index[indexer])
    return ((hist.iloc[-1]['Close'] - hist.iloc[indexer]['Close']) / hist.iloc[indexer]['Close']) * 100


class DataInterpreter:
    def __init__(self):
        self.tickerList = {}
        self.interpretMarketWatchData()

    def interpretMarketWatchData(self):
        marketwatchfile = open("MarketWatchListed.txt")
        for ticker in marketwatchfile.readlines():
            if settings.Settings.isInBlacklist(ticker):
                continue
            self.tickerList[ticker.rstrip()] = {}

    def interpretNasdaqData(self):
        exit(-1)

    def multiThreadTickerData(self):
        threadList = []
        for my_ticker in self.tickerList:
            threadList.append(myThread(my_ticker))
        for my_thread in threadList:
            my_thread.start()
        for my_thread in threadList:
            print(my_thread.return_dict)
            threadResult = my_thread.join(10.0)
            print("Result " + str(threadResult))
            print(len(threadResult))
            if len(threadResult) == 0:
                self.tickerList.pop(my_thread.my_ticker)
            else:
                print(my_thread.my_ticker)
                self.tickerList[my_thread.my_ticker] = threadResult
                print(self.tickerList[my_thread.my_ticker])
        print("Finished multithreading!")

    def getTickerData(self):
        print(self.tickerList)
        popList = []
        for ticker in self.tickerList:
            try:
                print("Ticker " + ticker + " pre-collection")
                ticker_data = yf.Ticker(ticker)
                dictionary = self.tickerList[ticker]
                # Info
                info = ticker_data.info
                dictionary[Info.longName] = info[Info.longName.value]

                hasHadNegativeYear(ticker_data)
                # Major Holders
                #           0                   1
                #   0   Previous Close          ##.##
                #   1   YTD Return              #.##%
                #   2   Expense Ratio (net)     #.##%
                #   3   Category                string
                #   4   Last Cap Gain           #.##
                #   5   Morningstar Rating      *****
                #   6   Morningstar Risk Rating High/Med/Low
                #   7   Sustainability Rating   ###
                major_holders = ticker_data.major_holders.get(1)
                dictionary[MajorHolders.ytd_return] = major_holders.get(MajorHolders.ytd_return.value).strip('%')
                dictionary[MajorHolders.morningstar_rating] = len(
                    major_holders.get(MajorHolders.morningstar_rating.value))
                dictionary[MajorHolders.category] = major_holders.get(MajorHolders.category.value)

                # Institutional
                #           0                   1
                #   0   Net Assets              #.##B
                #   1   Beta (5Y Monthly)       #.##
                #   2   Yield                   #.##%
                institutional = ticker_data.institutional_holders.get(1)
                dictionary[InstitutionalHolders.iyield] = institutional.get(InstitutionalHolders.iyield.value)

                dictionary["negativeYear"] = convertBoolToChar(hasHadNegativeYear(ticker_data))
                dictionary["four_weeks"] = get4Week(ticker_data)
                print("Ticker post-collection")
                print(self.tickerList[ticker])
                print(ticker)
            except:
                print("Error on ticker! " + ticker)
                popList.append(ticker)
        for ticker in popList:
            self.tickerList.pop(ticker)

    # Filter before scraping
    def primaryFilter(self):
        popList = []
        for my_ticker in self.tickerList:
            dictionary = self.tickerList[my_ticker]
            print(dictionary[MajorHolders.ytd_return])
            print(type(dictionary[MajorHolders.ytd_return]))
            print(dictionary[MajorHolders.morningstar_rating])
            print(type(dictionary[MajorHolders.morningstar_rating]))
            if '-' in dictionary[MajorHolders.ytd_return] or dictionary[MajorHolders.morningstar_rating] < 4:
                popList.append(my_ticker)
                print("Filtered: " + my_ticker)
        for my_ticker in popList:
            self.tickerList.pop(my_ticker)

    def scrapeForMissing(self):
        for ticker in self.tickerList:
            dictionary = self.tickerList[ticker]
            scrape_dict = data_grab.parseYFinance(ticker)
            dictionary[MarketWatch.one_year] = scrape_dict[MarketWatch.one_year.value]
            dictionary[MarketWatch.three_year] = scrape_dict[MarketWatch.three_year.value]
            dictionary[MarketWatch.five_year] = scrape_dict[MarketWatch.five_year.value]
            dictionary[MarketWatch.ten_year] = scrape_dict[MarketWatch.ten_year.value]
            print(dictionary)

    def secondaryFilter(self):
        popList = []
        for ticker in self.tickerList:
            dictionary = self.tickerList[ticker]
            if '-' in dictionary[MarketWatch.one_year] or '-' in dictionary[MarketWatch.three_year] \
                    or '-' in dictionary[MarketWatch.five_year] or '-' in dictionary[MarketWatch.ten_year]:
                popList.append(ticker)
                print("Filtered: " + ticker)
        for ticker in popList:
            self.tickerList.pop(ticker)

    def writeCSV(self):
        with open("tickers.csv", "w", newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(
                ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating',
                 'Neg. Yr'])
            for ticker in self.tickerList:
                dictionary = self.tickerList[ticker]
                print(dictionary)
                print(ticker)
                filewriter.writerow(
                    [ticker, dictionary[Info.longName], dictionary[MajorHolders.category],
                     dictionary[MajorHolders.ytd_return], dictionary['four_weeks'], dictionary[MarketWatch.one_year],
                     dictionary[MarketWatch.three_year], dictionary[MarketWatch.five_year],
                     dictionary[MarketWatch.ten_year], dictionary[InstitutionalHolders.iyield],
                     dictionary[MajorHolders.morningstar_rating],
                     dictionary['negativeYear']])
