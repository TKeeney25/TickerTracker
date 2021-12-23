import csv
import threading
import time
from tkinter import *

import pandas as pd
import yfinance as yf

import dataInterpreter
import main2
import settings


def yfinance():
    msft = yf.Ticker("AMTRX")
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    print("\n\nINFO")
    print(msft.info)
    # get historical market data
    hist = msft.history(period="1w")
    print("\n\nHIST")
    print(type(msft))
    print(hist)
    print(hist.info())
    # show actions (dividends, splits)
    print("\n\nACTIONS")
    print(msft.actions)

    # show dividends
    print("\n\nDIVIDENDS")
    print(msft.dividends)

    # show splits
    print("\n\nSPLITS")
    print(msft.splits)
    # show financials
    print("\n\nFINANCIALS")
    print(msft.financials)
    print("\n\nQFINANCIALS")
    print(msft.quarterly_financials)

    # show major holders
    print("\n\nMAJOR_HOLDERS")
    print(msft.major_holders)
    #    print(msft.major_holders.get(1).get(1))
    #    print(msft.major_holders.get(1).get(5))

    # show institutional holders
    print("\n\nINSTITUTIONAL")
    print(msft.institutional_holders)

    # show balance sheet
    print("\n\nBALANCE")
    print(msft.balance_sheet)
    print("\n\nQBALANCE")
    print(msft.quarterly_balance_sheet)

    # show cashflow
    print("\n\nCASHFLOW")
    print(msft.cashflow)
    print("\n\nQCASHFLOW")
    print(msft.quarterly_cashflow)

    # show earnings
    print("\n\nEARNINGS")
    print(msft.earnings)
    print("\n\nQEARNING")
    print(msft.quarterly_earnings)

    # show sustainability
    print("\n\nSUSTAIN")
    print(msft.sustainability)

    # show analysts recommendations
    print("\n\nRECOMMEND")
    print(msft.recommendations)

    # show next event (earnings, etc)
    print("\n\nCALENDAR")
    print(msft.calendar)

    # show ISIN code - *experimental*
    # ISIN = International Securities Identification Number
    print("\n\nISIN")
    print(msft.isin)

    # show options expirations
    print("\n\nOPTIONS")
    print(msft.options)

    # show news
    print("\n\nNEWS")
    print(msft.news)
    # get option chain for specific expiration
    # opt = msft.option_chain('YYYY-MM-DD')
    # print(opt)
    # data available via: opt.calls, opt.puts


class MyWindow:
    def __init__(self, win):
        self.introLabel = Label(window, text="Ticker Tracker", fg='red', font=("Helvetica", 16))
        self.introLabel.place(x=60, y=50)
        self.startButton = Button(window, text="Start", fg='blue', command=self.loadingTickers)
        self.startButton.place(x=80, y=100)

    def defaultLoading(self):
        self.loadingLabel = Label(window, text="Loading")
        self.loadingLabel.place(x=60, y=50)

    def loadingTickers(self):
        self.defaultLoading()
        # data_grab.startup()
        # data_grab.parseMarketWatch()


'''
def threadyTesty(my_ticker: main2.MyTicker) -> bool:
    start_time = time.time()
    print("Start " + my_ticker.symbol)
    print("\tPrimary Filter")
    market_data = main2.getFullMarketWatchData(my_ticker.symbol)
    my_ticker.full_name = market_data[main2.MarketWatch.full_name]
    my_ticker.one_year = market_data[main2.MarketWatch.one_year]
    my_ticker.three_year = market_data[main2.MarketWatch.three_year]
    my_ticker.five_year = market_data[main2.MarketWatch.five_year]
    my_ticker.ten_year = market_data[main2.MarketWatch.ten_year]
    if not main2.passesFilter(my_ticker):
        print("Filtered")
        return False
    print("\tPrimary Filter took " + str(time.time() - start_time))
    start_time = time.time()
    print("\tSecondary Filter")
    major_holders = main2.getYFinanceMajorHolders(my_ticker.my_ticker)
    my_ticker.rating = major_holders[main2.MajorHolders.morningstar_rating]
    my_ticker.year_to_date = major_holders[main2.MajorHolders.ytd_return]
    my_ticker.category = major_holders[main2.MajorHolders.category]
    if not main2.passesFilter(my_ticker) or main2.containsDefaults(my_ticker):
        print("Filtered")
        return False
    print("\tSecondary Filter took " + str(time.time() - start_time))
    start_time = time.time()
    print("\tFinal Data pass")
    my_ticker.four_week = main2.getYFinanceFourWeeks(my_ticker.my_ticker)
    institutional_holders = main2.getYFinanceInstitutionalHolders(my_ticker.my_ticker)
    my_ticker.my_yield = institutional_holders[main2.InstitutionalHolders.iyield]
    my_ticker.negative_year = main2.getYFinanceNegativeYear(my_ticker.my_ticker)
    print("\tFinal Data pass took " + str(time.time() - start_time))
    return True
'''


def speed_test():
    print('Init MyTicker')
    start_time2 = time.time()
    my_ticker = main2.MyTicker('AMTIX')
    print(time.time() - start_time2)
    print("Start MarketWatch")
    start_time2 = time.time()
    main2.getFullMarketWatchData('AMTIX')
    print(time.time() - start_time2)
    print("Start getYFinanceInfo")
    start_time2 = time.time()
    main2.getYFinanceInfo(my_ticker.my_ticker)
    print(time.time() - start_time2)
    print("Start getYFinanceFourWeeks")
    start_time2 = time.time()
    main2.getYFinanceFourWeeks(my_ticker.my_ticker)
    print(time.time() - start_time2)
    print("Start getYFinanceNegativeYear")
    start_time2 = time.time()
    main2.getYFinanceNegativeYear(my_ticker.my_ticker)
    print(time.time() - start_time2)
    print("Start getYFinanceMajorHolders")
    start_time2 = time.time()
    main2.getYFinanceMajorHolders(my_ticker.my_ticker)
    print(time.time() - start_time2)
    print("Start getYFinanceInstitutionalHolders")
    start_time2 = time.time()
    main2.getYFinanceInstitutionalHolders(my_ticker.my_ticker)
    print(time.time() - start_time2)


class TestThread(threading.Thread):
    def __init__(self, name, my_ticker: main2.MyTicker):
        super().__init__(name=name)
        self.my_ticker = my_ticker
        self.success = True

    def run(self):
        exit(-1)
        # self.success = threadyTesty(self.my_ticker)

    def join(self, timeout=None) -> bool:
        threading.Thread.join(self, timeout)
        return self.success


def start():
    failed_csv = open('failedTickers.csv', "a", newline='')
    failed_writer = csv.writer(failed_csv, delimiter=',',
                               quotechar='|', quoting=csv.QUOTE_MINIMAL)
    failed_writer.writerow(
        ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating',
         'Neg. Yr'])
    with open("tickers.csv", "r+", newline='') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        reader = csv.reader(csvfile)
        read = []
        last_ticker = ''
        for row in reader:
            read.append(row)
        if len(read) == 0:
            filewriter.writerow(
                ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating',
                 'Neg. Yr'])
        else:
            last_ticker: str = read[-1][0]
        if 'Ticker' in last_ticker:
            last_ticker = ''
        market_watch_file = open("MarketWatchListed.txt")
        print("Get All Tickers")
        if len(last_ticker) == 0:
            reached_last_ticker = True
        else:
            reached_last_ticker = False
            print("Starting from: " + last_ticker)
        start_pos = 0
        start_time = time.time()
        for symbol in market_watch_file.readlines():
            symbol = symbol.rstrip()
            if settings.Settings.isInFullBlacklist(symbol) or not reached_last_ticker:
                if last_ticker in symbol:
                    reached_last_ticker = True
                start_pos += 1
                continue
            my_ticker = main2.MyTicker(symbol)
            start_time2 = time.time()
            print("Start: " + my_ticker.symbol)
            runtime = time.time() - start_time
            print("Runtime: " + time.strftime("%H:%M:%S", time.gmtime(runtime)))
            print("\tPrimary Filter")
            market_data = main2.getFullMarketWatchData(my_ticker.symbol)
            my_ticker.full_name = market_data[main2.MarketWatch.full_name]
            my_ticker.one_year = market_data[main2.MarketWatch.one_year]
            my_ticker.three_year = market_data[main2.MarketWatch.three_year]
            my_ticker.five_year = market_data[main2.MarketWatch.five_year]
            my_ticker.ten_year = market_data[main2.MarketWatch.ten_year]
            if main2.hasMissingData(my_ticker):
                negative_year_data = main2.getYFinanceNegativeYear(my_ticker.my_ticker)
                if negative_year_data[0]:
                    my_ticker.negative_year = negative_year_data[1]
                else:
                    settings.Settings.AddTimebomb(my_ticker.symbol, negative_year_data[1])
                    continue
            if main2.hasMissingData(my_ticker) or not main2.passesFilter(my_ticker):
                print("Filtered")
                failed_writer.writerow(my_ticker.toCSV())
                failed_csv.flush()
                continue
            print("\tPrimary Filter took " + str(time.time() - start_time2))
            start_time2 = time.time()
            print("\tSecondary Filter")
            major_holders = main2.getYFinanceMajorHolders(my_ticker.my_ticker)
            info = main2.getYFinanceInfo(my_ticker.my_ticker)
            if not major_holders or not info:
                settings.Settings.AddToBlacklist(my_ticker.symbol)
                continue
            my_ticker.rating = info[main2.Info.morningstar_rating]
            my_ticker.year_to_date = major_holders[main2.MajorHolders.ytd_return]
            my_ticker.category = major_holders[main2.MajorHolders.category]
            if not main2.passesFilter(my_ticker):
                print("Filtered")
                failed_writer.writerow(my_ticker.toCSV())
                failed_csv.flush()
                continue
            print("\tSecondary Filter took " + str(time.time() - start_time2))
            start_time2 = time.time()
            print("\tFinal Data pass")
            my_ticker.four_week = main2.getYFinanceFourWeeks(my_ticker.my_ticker)
            institutional_holders = main2.getYFinanceInstitutionalHolders(my_ticker.my_ticker)
            my_ticker.my_yield = institutional_holders[main2.InstitutionalHolders.iyield]
            negative_year_data = main2.getYFinanceNegativeYear(my_ticker.my_ticker)
            if negative_year_data[0]:
                my_ticker.negative_year = negative_year_data[1]
            else:
                settings.Settings.AddTimebomb(my_ticker.symbol, negative_year_data[1])
                continue
            my_ticker.negative_year = dataInterpreter.convertBoolToChar(
                main2.getYFinanceNegativeYear(my_ticker.my_ticker)[1])
            if main2.containsDefaults(my_ticker):
                print("Filtered")
                failed_writer.writerow(my_ticker.toCSV())
                failed_csv.flush()
                continue
            filewriter.writerow(my_ticker.toCSV())
            csvfile.flush()
            print("\tFinal Data pass took " + str(time.time() - start_time2))
        '''
        threads = []
        print("Get threads")
        start_time2 = time.time()
        for my_ticker in ticker_list:
            threads.append(TestThread(my_ticker.symbol, my_ticker))
        print("Tickers took " + str(time.time() - start_time2))
        print("Start threads")
        start_time2 = time.time()
        for my_thread in threads:
            my_thread.start()
        print("Tickers took " + str(time.time() - start_time2))
        print("Join threads")
        start_time2 = time.time()
        for my_thread in threads:
            result = my_thread.join(10000)
            #if not result:
            #    print("Removing " + str(my_thread.my_ticker))
            #   ticker_list.remove(my_thread.my_ticker)
        print("Tickers took " + str(time.time() - start_time2))
        '''
    # failed_csv.close()

#yfinance()
#exit(-1)
print('Full Time')
overall_time = time.time()
start()
print('End Time')
print(time.strftime("%H:%M:%S", time.gmtime(time.time() - overall_time)))
exit(-1)
window = Tk()
myWin = MyWindow(window)
window.title('Hello Python')
window.geometry("300x200+10+20")
interpret = dataInterpreter.DataInterpreter()
# interpret.multiThreadTickerData()
interpret.getTickerData()
interpret.primaryFilter()
interpret.scrapeForMissing()
interpret.secondaryFilter()
interpret.writeCSV()
window.mainloop()
print("\n\n\n\n\n\nexiting main loop")
settings.Settings.SaveSettings()
