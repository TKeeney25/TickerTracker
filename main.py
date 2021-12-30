import enum
import json
from datetime import datetime, date, timedelta
from typing import Union

from dateutil.relativedelta import relativedelta

import settings
from json_interpreter import getAllFunds
from csv_writer import CSVWriter
import api_caller


# region 'Enums'


class FeesExpensesInvestment(enum.Enum):
    twelve_b_one = 'twelveBOne'


class QuoteType(enum.Enum):
    long_name = 'longName'


class TrailingReturns(enum.Enum):
    year_to_date = 'ytd'
    one_month = 'oneMonth'
    one_year = 'oneYear'
    three_year = 'threeYear'
    five_year = 'fiveYear'
    ten_year = 'tenYear'


class SummaryDetail(enum.Enum):
    my_yield = 'yield'


class DefaultKeyStatistics(enum.Enum):
    morningstar_overall_rating = 'morningStarOverallRating'
    legal_type = 'legalType'
    fund_inception_date = 'fundInceptionDate'


class FundPerformance(enum.Enum):
    trailingReturns = 'trailingReturns'
    annual_total_returns = 'annualTotalReturns'


class FundProfile(enum.Enum):
    fund_inception_date = 'fundInceptionDate'
    category_name = 'categoryName'
    brokerages = 'brokerages'
    legal_type = 'legalType'
    fees_expenses_investment = 'feesExpensesInvestment'


class Fund(enum.Enum):
    default_key_statistics = 'defaultKeyStatistics'
    fundPerformance = 'fundPerformance'
    fund_profile = 'fundProfile'
    quote_type = 'quoteType'
    summary_detail = 'summaryDetail'


class Format(enum.Enum):
    raw = 'raw'
    formatted = 'fmt'
    long_formatted = 'longFmt'


# endregion


def boolToStr(conditional: bool) -> str:
    if conditional:
        return 'Y'
    else:
        return 'N'


class MyTicker:
    default_string = ''
    default_float = float('-inf')
    default_int = -1

    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.full_name: str = self.default_string
        self.category: str = self.default_string
        self.year_to_date: float = self.default_float
        self.one_month: float = self.default_float
        self.one_year: float = self.default_float
        self.three_year: float = self.default_float
        self.five_year: float = self.default_float
        self.ten_year: float = self.default_float
        self.my_yield: float = self.default_float
        self.rating: int = self.default_int
        self.negative_year: bool = False
        self.legal_type: str = self.default_string
        self.twelve_b_one: float = 0
        self.brokerages: list = []

    def toCSV(self) -> []:
        return [self.symbol, self.full_name, self.category, self.year_to_date, self.one_month, self.one_year,
                self.three_year, self.five_year, self.ten_year, self.my_yield, self.rating,
                boolToStr(self.negative_year)]

    def toVerboseCSV(self) -> []:
        return self.toCSV() + [self.legal_type, self.twelve_b_one, str(self.brokerages).replace(',', '')]

    def __str__(self):
        return 'Symbol: %s, Full Name: %s, Category: %s, YTD: %s, 4-Week: %s, 1-Year: %s, 3-Year: %s, 5-Year: %s, ' \
               '10-Year: %s, Yield: %s, Morningstar Rating: %s, Negative Year: %s, Legal Type: %s, 12 b-1: %s,' \
               ' Brokerages: %s' \
               % (self.symbol, self.full_name, self.category, str(self.year_to_date),
                  str(self.one_month), str(self.one_year), str(self.three_year), str(self.five_year),
                  str(self.ten_year), str(self.my_yield), str(self.rating), str(self.negative_year),
                  self.legal_type, str(self.twelve_b_one), str(self.brokerages).replace(',', ''))

    def has_defaults(self) -> [Union[bool, str]]:
        if len(self.full_name) == 0:
            return [False, 'Contains Default Values']
        if self.year_to_date == self.default_float:
            return [False, 'Contains Default Values']
        if self.one_year == self.default_float:
            return [False, 'Contains Default Values']
        if self.three_year == self.default_float:
            return [False, 'Contains Default Values']
        if self.five_year == self.default_float:
            return [False, 'Contains Default Values']
        if self.ten_year == self.default_float:
            return [False, 'Contains Default Values']
        if self.my_yield == self.default_float:
            return [False, 'Contains Default Values']
        if self.rating == self.default_int:
            return [False, 'Contains Default Values']
        return [True, '']

    def passes_filter(self) -> [Union[bool, str]]:
        defaults = self.has_defaults()
        if not defaults[0]:
            return defaults
        if len(self.brokerages) > 0:
            fail = True
            for broker in self.brokerages:
                if 'LPL SWM' in broker:
                    fail = False
                    break
            if fail:
                return [False, 'LPL SWM not in brokerages']
        if self.rating is None or self.rating < 4:
            return [False, 'Has Morningstar rating of: ' + str(self.rating)]
        if self.ten_year <= 0:
            return [False, 'Has a ten year return of: ' + str(self.ten_year)]
        if self.five_year <= 0:
            return [False, 'Has a ten year return of: ' + str(self.five_year)]
        if self.three_year <= 0:
            return [False, 'Has a ten year return of: ' + str(self.three_year)]
        if self.one_year <= 0:
            return [False, 'Has a ten year return of: ' + str(self.one_year)]
        if self.twelve_b_one > 0:
            return [False, 'Has a 12b-1 of: ' + str(self.twelve_b_one)]
        return [True, '']


def loadSymbols() -> {}:
    with open("symbols.json", "r") as json_file:
        json_load = None
        if len(json_file.readlines()) > 0:
            json_file.seek(0)
            json_load = json.load(json_file)
    if json_load is None or (
            datetime.strptime(json_load['date'], settings.TIME_STRING) + timedelta(days=30)).date() < date.today():
        with open("symbols.json", "w") as json_file:
            json_load = {"date": date.today().strftime(settings.TIME_STRING), "symbols": getAllFunds()}
            print(json_load)
            json_file.write(json.dumps(json_load, indent=4, sort_keys=True))
    return json_load


def hasHadNegativeYear(returns: list, year_span=10) -> bool:
    current_year = date.today().year
    year_range = range(current_year - year_span, current_year)
    for single_return in returns:
        if int(single_return['year']) in year_range:
            if len(single_return['annualValue']) > 0:
                if float(single_return['annualValue'][Format.raw.value]) < 0:
                    return True
    return False


def shouldBeFiltered(symbol: str) -> bool:
    if settings.isInBlacklist(symbol):
        return True
    if '^' in symbol:
        return True
    if '-' in symbol:
        return True
    return False


def is_too_young(time: str) -> [Union[bool, str]]:
    time_plus_ten = datetime.strptime(time, settings.TIME_STRING) + relativedelta(years=10)
    today = date.today()
    if time_plus_ten > datetime(today.year, today.month, today.day):
        return [True, time_plus_ten.strftime(settings.TIME_STRING)]
    return [False, '']


def processSymbols():
    headers = ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating', 'Neg. Yr']
    failed_headers = headers + ['12b-1', 'Brokerages', 'Failed Reason']
    tickers_csv = CSVWriter('tickers.csv', headers)
    failed_tickers_csv = CSVWriter('failedTickers.csv', failed_headers)
    symbol_list = loadSymbols()['symbols']
    my_ticker = MyTicker('')
    for symbol in symbol_list:
        try:
            symbol = symbol.rstrip()
            print('Symbol ' + symbol)
            if shouldBeFiltered(symbol):
                print('Filtered')
                continue
            api_response = api_caller.getFundInfo(symbol)
            if '200' not in str(api_response):
                settings.AddToLog('processSymbols()', symbol, settings.LogTypes.debug, str(api_response))
                if '432' in str(api_response):
                    break
                continue
            symbol_dict = json.loads(api_response.text)
            my_ticker = MyTicker(symbol)
            ''' FUND PROFILE '''
            fund_profile = symbol_dict[Fund.fund_profile.value]
            if 'err' in fund_profile:
                print("Fund profile not found!")
                settings.AddToLog('Default Key Statistics', symbol, settings.LogTypes.error, str(fund_profile))
                today = date.today()
                settings.AddTimeBomb(
                    symbol, (datetime(today.year, today.month, today.day) + relativedelta(years=9)
                             ).strftime(settings.TIME_STRING))
                continue
            else:
                print('fund profile ' + str(fund_profile))
                my_ticker.brokerages = fund_profile[FundProfile.brokerages.value]
                my_ticker.category = fund_profile[FundProfile.category_name.value]
                my_ticker.legal_type = fund_profile[FundProfile.legal_type.value]
                twelve_b_one = (fund_profile[
                    FundProfile.fees_expenses_investment.value][FeesExpensesInvestment.twelve_b_one.value])
                if len(twelve_b_one) > 0:
                    my_ticker.twelve_b_one = float(fund_profile[FundProfile.fees_expenses_investment.value]
                                                   [FeesExpensesInvestment.twelve_b_one.value][
                                                       Format.formatted.value].strip('%'))
            ''' DEFAULT KEY STATISTICS'''
            default_key_statistics = symbol_dict[Fund.default_key_statistics.value]
            if 'err' in default_key_statistics:
                print('Default Key Statistics not found!')
                settings.AddToLog('Default Key Statistics', symbol, settings.LogTypes.error, str(default_key_statistics))
                continue
            else:
                print('default key statistics ' + str(default_key_statistics))
                is_too_young_data = is_too_young(
                    default_key_statistics[DefaultKeyStatistics.fund_inception_date.value][Format.formatted.value])
                if is_too_young_data[0]:
                    settings.AddTimeBomb(symbol, is_too_young_data[1])
                    failed_tickers_csv.write(my_ticker.toVerboseCSV() +
                                             ["<10 years old. Will be 10 on " + is_too_young_data[1]])
                    continue
                if my_ticker.legal_type is None or 'Exchange Traded Fund' not in my_ticker.legal_type:
                    my_ticker.rating = int(default_key_statistics[
                                               DefaultKeyStatistics.morningstar_overall_rating.value][
                                               Format.formatted.value])
                else:
                    my_ticker.rating = api_caller.getMorningstarRating(my_ticker.symbol)
            ''' FUND PERFORMANCE '''
            fund_performance = symbol_dict[Fund.fundPerformance.value]
            if 'err' in fund_performance:
                print('Fund performance not found!')
                settings.AddToLog('Fund Performance', symbol, settings.LogTypes.error, str(fund_performance))
                continue
            else:
                print('fund performance ' + str(fund_performance))
                trailing_returns = fund_performance[FundPerformance.trailingReturns.value]
                print('trailing returns ' + str(trailing_returns))
                my_ticker.year_to_date = float(
                    trailing_returns[TrailingReturns.year_to_date.value][Format.formatted.value].strip('%'))
                my_ticker.one_month = float(
                    trailing_returns[TrailingReturns.one_month.value][Format.formatted.value].strip('%'))
                my_ticker.one_year = float(
                    trailing_returns[TrailingReturns.one_year.value][Format.formatted.value].strip('%'))
                my_ticker.three_year = float(
                    trailing_returns[TrailingReturns.three_year.value][Format.formatted.value].strip('%'))
                my_ticker.five_year = float(
                    trailing_returns[TrailingReturns.five_year.value][Format.formatted.value].strip('%'))
                my_ticker.ten_year = float(
                    trailing_returns[TrailingReturns.ten_year.value][Format.formatted.value].strip('%'))
                my_ticker.negative_year = hasHadNegativeYear(
                    fund_performance[FundPerformance.annual_total_returns.value]['returns'])
            ''' QUOTE TYPE'''
            quote_type = symbol_dict[Fund.quote_type.value]
            if 'err' in quote_type:
                print('Quote Type not found!')
                settings.AddToLog('Quote Type', symbol, settings.LogTypes.error, str(quote_type))
                continue
            else:
                print('Quote Type ' + str(quote_type))
                my_ticker.full_name = quote_type[QuoteType.long_name.value]
            ''' SUMMARY DETAIL '''
            summary_detail = symbol_dict[Fund.summary_detail.value]
            if 'err' in summary_detail or len(summary_detail) == 0:
                print('Summary Detail not found!')
                settings.AddToLog('Summary Detail', symbol, settings.LogTypes.error, str(summary_detail))
                continue
            else:
                print("Summary detail " + str(summary_detail))
                my_ticker.my_yield = float(
                    summary_detail[SummaryDetail.my_yield.value][Format.formatted.value].strip('%'))
            print(my_ticker)
            print(my_ticker.passes_filter())
            print(symbol_dict)
            if my_ticker.passes_filter()[0]:
                tickers_csv.write(my_ticker.toCSV())
            else:
                failed_tickers_csv.write(my_ticker.toVerboseCSV() + [my_ticker.passes_filter()[1]])
        except KeyError as exception:
            settings.AddToLog('processSymbols()', symbol, settings.LogTypes.error)
            failed_tickers_csv.write(my_ticker.toVerboseCSV() + ['Threw exception during execution: ' + str(exception)])


processSymbols()
