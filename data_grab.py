import string
from ftplib import FTP

import urllib3
from bs4 import BeautifulSoup

import dataInterpreter


def startup():
    print("Acquiring Tickers...")
    # First we need to get a full list of all the tickers
    ftp = FTP('ftp.nasdaqtrader.com')
    # This logs us in anonymously
    ftp.login()
    # Get the files
    ftp.cwd('/SymbolDirectory/')
    file1_name = 'nasdaqlisted.txt'
    file2_name = 'otherlisted.txt'
    # Open local files for writing
    my_file1 = open(file1_name, 'wb')
    my_file2 = open(file2_name, 'wb')
    # Write to the local files from FTP (in binary)
    ftp.retrbinary('RETR ' + file1_name, my_file1.write, 1024)
    ftp.retrbinary('RETR ' + file2_name, my_file2.write, 1024)
    # Close files and connections
    ftp.quit()
    my_file1.close()
    my_file2.close()
    print("Tickers Acquired!")


def parseMarketWatch():
    http = urllib3.PoolManager()
    my_file = open("MarketWatchListed.txt", "w")

    for character in string.ascii_uppercase:
        r = http.request('GET', 'https://www.marketwatch.com/tools/mutual-fund/list/' + character)
        soup = BeautifulSoup(r.data, 'lxml')
        for x in soup.find_all("td"):
            if len(x.text) <= 10:
                print(x.text)
                my_file.write(x.text + '\n')

    my_file.close()


def parseYFinance(ticker: string) -> dict:
    market = dataInterpreter.MarketWatch
    return_dict = {market.year_to_date.value: 0, market.one_year.value: 0, market.three_year.value: 0,
                   market.five_year.value: 0, market.ten_year.value: 0}
    list_thing = [market.year_to_date.value, market.one_year.value, market.three_year.value, market.five_year.value,
                  market.ten_year.value]
    list_count = 0
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://www.marketwatch.com/investing/fund/' + ticker)
    soup = BeautifulSoup(r.data, 'lxml')
    print(soup)
    for x in soup.find_all('td'):
        if x.has_attr('data-fund-return'):
            return_dict[list_thing[list_count]] = x.text
            print(x.text)
            list_count += 1
    print(return_dict)
    return return_dict
