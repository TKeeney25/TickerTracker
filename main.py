import enum
import json
from datetime import datetime, date, timedelta

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


class FundPerformance(enum.Enum):
    trailingReturns = 'trailingReturns'
    annual_total_returns = 'annualTotalReturns'


class FundProfile(enum.Enum):
    fund_inception_date = 'fundInceptionDate'
    category_name = 'categoryName'
    brokerages = 'brokerages'
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
        self.brokerage: list = []
        self.year_to_date: float = self.default_float
        self.one_month: float = self.default_float
        self.one_year: float = self.default_float
        self.three_year: float = self.default_float
        self.five_year: float = self.default_float
        self.ten_year: float = self.default_float
        self.my_yield: float = self.default_float
        self.twelve_b_one: float = 0
        self.rating: int = self.default_int
        self.negative_year: bool = False

    def toCSV(self) -> []:
        return [self.symbol, self.full_name, self.category, self.year_to_date, self.one_month, self.one_year,
                self.three_year, self.five_year, self.ten_year, self.my_yield, self.rating,
                boolToStr(self.negative_year)]

    def __str__(self):
        return 'Symbol: %s, Full Name: %s, Category: %s, 12 b-1: %s YTD: %s, 4-Week: %s, 1-Year: %s, 3-Year: %s,' \
               ' 5-Year: %s, 10-Year: %s, Yield: %s, Morningstar Rating: %s, Negative Year: %s, Brokerages: %s' \
               % (self.symbol, self.full_name, self.category, str(self.twelve_b_one), str(self.year_to_date),
                  str(self.one_month), str(self.one_year), str(self.three_year), str(self.five_year),
                  str(self.ten_year), str(self.my_yield), str(self.rating), str(self.negative_year),
                  str(self.brokerage))

    def passes_filter(self) -> bool:
        if 'LPL SWM' not in self.brokerage:
            return False
        if self.rating < 4:
            return False
        if self.ten_year <= 0:
            return False
        if self.five_year <= 0:
            return False
        if self.three_year <= 0:
            return False
        if self.one_year <= 0:
            return False
        if self.twelve_b_one > 0:
            return False
        return True


def loadSymbols() -> {}:
    with open("symbols.json", "r") as json_file:
        json_load = None
        if len(json_file.readlines()) > 0:
            json_file.seek(0)
            json_load = json.load(json_file)
    if json_load is None or (
            datetime.strptime(json_load['date'], "%m-%d-%Y") + timedelta(days=30)).date() < date.today():
        with open("symbols.json", "w") as json_file:
            json_load = {"date": date.today().strftime("%m-%d-%Y"), "symbols": getAllFunds()}
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


def processSymbols():
    headers = ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating', 'Neg. Yr']
    with CSVWriter('tickers.csv', headers) as tickers_csv:
        with CSVWriter('failedTickers.csv', headers) as failed_tickers_csv:
            symbol_list = loadSymbols()['symbols']
            for my_symbol in symbol_list:
                symbol_dict = api_caller.getFundInfo(my_symbol.rstrip())
                my_ticker = MyTicker(my_symbol)
                ''' DEFAULT KEY STATISTICS'''
                default_key_statistics = symbol_dict[Fund.default_key_statistics.value]
                my_ticker.rating = (default_key_statistics[
                    DefaultKeyStatistics.morningstar_overall_rating.value][Format.formatted.value])
                ''' FUND PROFILE '''
                fund_profile = symbol_dict[Fund.fund_profile.value]
                my_ticker.brokerage = fund_profile[FundProfile.brokerages.value]
                my_ticker.category = fund_profile[FundProfile.category_name.value]
                twelve_b_one = (fund_profile[
                    FundProfile.fees_expenses_investment.value][FeesExpensesInvestment.twelve_b_one.value])
                if len(twelve_b_one) > 0:
                    my_ticker.twelve_b_one = float(fund_profile[FundProfile.fees_expenses_investment.value]
                                                   [FeesExpensesInvestment.twelve_b_one.value][
                                                       Format.formatted.value].strip('%'))
                ''' FUND PERFORMANCE '''
                fund_performance = symbol_dict[Fund.fundPerformance.value]
                trailing_returns = fund_performance[FundPerformance.trailingReturns.value]
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
                my_ticker.full_name = quote_type[QuoteType.long_name.value]
                ''' SUMMARY DETAIL '''
                summary_detail = symbol_dict[Fund.summary_detail.value]
                my_ticker.my_yield = float(
                    summary_detail[SummaryDetail.my_yield.value][Format.formatted.value].strip('%'))
                print(my_ticker)
                print(my_ticker.passes_filter())
                print(symbol_dict)
                if my_ticker.passes_filter():
                    tickers_csv.write(my_ticker.toCSV())
                else:
                    failed_tickers_csv.write(my_ticker.toCSV())
