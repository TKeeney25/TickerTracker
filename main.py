import enum
import json
import os
import sys
import threading
import time
from datetime import datetime, date, timedelta
from functools import partial
from queue import Queue
from typing import Union

import pyjokes
from dateutil.relativedelta import relativedelta
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager

import api_caller
import settings
import json_interpreter
from csv_writer import CSVWriter

Window.size = (1280, 960)


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
        return [self.symbol, self.full_name.replace(',', ''), self.category, self.year_to_date, self.one_month,
                self.one_year, self.three_year, self.five_year, self.ten_year, self.my_yield, self.rating,
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
        return [True, 'Passed']


def loadSymbols(force_refresh=False) -> {}:
    if not os.path.exists(settings.SYMBOL_FILE) or force_refresh:
        open(settings.SYMBOL_FILE, 'w').close()
    with open(settings.SYMBOL_FILE, "r") as json_file:
        json_load = None
        if len(json_file.readlines()) > 0:
            json_file.seek(0)
            json_load = json.load(json_file)
    if json_load is None or (
            datetime.strptime(json_load['date'], settings.TIME_STRING) + timedelta(days=30)).date() < date.today() or (
            not json_load[json_interpreter.Symbols.complete.value][json_interpreter.Complete.is_complete.value]):
        json_load = json_interpreter.Funds().getAllFunds()
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
    if settings.isInWhitelist(symbol):
        return False
    if settings.isInBlacklist(symbol):
        return True
    if '^' in symbol:
        return True
    if '-' in symbol:
        return True
    return False


def is_too_young(my_time='') -> [Union[bool, str]]:
    today = date.today()
    datetime_today = datetime(today.year, today.month, today.day)
    if len(my_time) > 0:
        time_plus_ten = datetime.strptime(my_time, settings.TIME_STRING) + relativedelta(years=10)
    else:
        time_plus_ten = datetime_today + relativedelta(days=1)
    if time_plus_ten > datetime_today:
        return [True, time_plus_ten.strftime(settings.TIME_STRING)]
    return [False, '']


is_overwrite = False
is_refresh_tickers = False


def processSymbols():
    try:
        funds_read = 0
        settings.current_stage = 'Starting...'
        headers = ['Ticker', 'Name', 'Category', 'YTD', '4W', '1Y', '3Y', '5Y', '10Y', 'Yield', 'Rating', 'Neg. Yr']
        failed_headers = headers + ['12b-1', 'Brokerages', 'Failed Reason']
        for i in range(2):
            tickers_csv = \
                CSVWriter(settings.GetFilePath() + '\\' + settings.GetFileName(), headers, is_overwrite)
            failed_tickers_csv = \
                CSVWriter(settings.GetFilePath() + '\\' + settings.GetFailedFileName(), failed_headers, is_overwrite)
        symbol_list = loadSymbols(is_refresh_tickers)['symbols']
        my_ticker = MyTicker('')
        total_funds = len(symbol_list)
        time_start = time.time()
        for symbol in symbol_list:
            if settings.pause_event.is_set() or settings.exit_event.is_set():
                settings.log('Paused')
                pause_start = time.time()
                while settings.pause_event.is_set() or settings.exit_event.is_set():
                    time.sleep(.1)
                    if settings.exit_event.is_set():
                        raise settings.EndExecution()
                time_start += time.time() - pause_start
            try:
                symbol = symbol.rstrip()
                settings.current_stage = "Processing: " + symbol
                settings.log("Processing: " + symbol)
                time_diff = time.time() - time_start
                settings.runtime = str(time.strftime("%H:%M:%S", time.gmtime(time_diff)))
                if funds_read != 0:
                    settings.time_remaining = str(time.strftime("%H:%M:%S", time.gmtime(
                        (time_diff / funds_read) * (total_funds - funds_read))))
                funds_read += 1
                if shouldBeFiltered(symbol):
                    settings.log('Filtered ' + symbol)
                    continue
                if tickers_csv.isInCSV(symbol) or failed_tickers_csv.isInCSV(symbol):
                    settings.log(symbol + ' already obtained. Skipping...')
                    continue
                api_response = api_caller.getFundInfo(symbol)
                if '200' not in str(api_response):
                    settings.log('Api Response of %s for %s. Skipping...' % (api_response, symbol))
                    settings.AddToLog('processSymbols()', symbol, settings.LogTypes.debug, str(api_response))
                    failed_tickers_csv.write(my_ticker.toVerboseCSV() + ["API Response of " + str(api_response)])
                    if '432' in str(api_response):
                        raise Exception('Out of API Calls! Stopping!')
                    if '401' in str(api_response) or '403' in str(api_response):
                        raise Exception('Incorrect API Key! Stopping!')
                    continue
                symbol_dict = json.loads(api_response.text)
                my_ticker = MyTicker(symbol)
                default_key_statistics = symbol_dict[Fund.default_key_statistics.value]
                if DefaultKeyStatistics.fund_inception_date.value in default_key_statistics \
                        and len(default_key_statistics[DefaultKeyStatistics.fund_inception_date.value]) > 0:
                    is_too_young_data = is_too_young(
                        default_key_statistics[DefaultKeyStatistics.fund_inception_date.value][Format.formatted.value])
                else:
                    is_too_young_data = is_too_young()
                if is_too_young_data[0]:
                    settings.AddTimeBomb(symbol, is_too_young_data[1])
                    failed_tickers_csv.write(my_ticker.toVerboseCSV() +
                                             ["<10 years old. Will be 10 on " + is_too_young_data[1]])
                    settings.log('%s is too young. Will be old enough on %s' % (symbol, is_too_young_data[1]))
                    continue
                quote_type = symbol_dict[Fund.quote_type.value]
                fund_profile = symbol_dict[Fund.fund_profile.value]
                fund_performance = symbol_dict[Fund.fundPerformance.value]
                summary_detail = symbol_dict[Fund.summary_detail.value]
                my_ticker.brokerages = fund_profile[FundProfile.brokerages.value]
                my_ticker.category = fund_profile[FundProfile.category_name.value]
                my_ticker.legal_type = fund_profile[FundProfile.legal_type.value]
                twelve_b_one = (fund_profile[
                    FundProfile.fees_expenses_investment.value][FeesExpensesInvestment.twelve_b_one.value])
                if len(twelve_b_one) > 0:
                    my_ticker.twelve_b_one = float(fund_profile[FundProfile.fees_expenses_investment.value]
                                                   [FeesExpensesInvestment.twelve_b_one.value][
                                                       Format.formatted.value].strip('%'))
                is_too_young_data = is_too_young(
                    default_key_statistics[DefaultKeyStatistics.fund_inception_date.value][Format.formatted.value])
                if is_too_young_data[0]:
                    settings.AddTimeBomb(symbol, is_too_young_data[1])
                    failed_tickers_csv.write(my_ticker.toVerboseCSV() +
                                             ["<10 years old. Will be 10 on " + is_too_young_data[1]])
                    settings.log('%s is too young. Will be old enough on %s' % (symbol, is_too_young_data[1]))
                    continue
                if my_ticker.legal_type is None or 'Exchange Traded Fund' not in my_ticker.legal_type:
                    my_ticker.rating = int(default_key_statistics[
                                               DefaultKeyStatistics.morningstar_overall_rating.value][
                                               Format.raw.value])
                else:
                    my_ticker.rating = api_caller.getMorningstarRating(my_ticker.symbol)
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
                my_ticker.full_name = quote_type[QuoteType.long_name.value]
                my_ticker.my_yield = float(
                    summary_detail[SummaryDetail.my_yield.value][Format.formatted.value].strip('%'))
                if my_ticker.passes_filter()[0]:
                    settings.log('%s complete' % symbol)
                    tickers_csv.write(my_ticker.toCSV())
                else:
                    settings.log('Filtered %s' % symbol)
                    failed_tickers_csv.write(my_ticker.toVerboseCSV() + [my_ticker.passes_filter()[1]])
            except KeyError as exception:
                settings.log('%s threw error %s!' % (symbol, str(exception)), settings.LogTypes.error)
                failed_tickers_csv.write(my_ticker.toVerboseCSV() + ['Threw exception during execution: ' + str(exception)])
        settings.current_stage = 'Done!'
    except settings.EndExecution:
        settings.log('Stopped')
        settings.current_stage = 'Stopped'
    except Exception as exception:
        settings.log('Thread threw error: %s' % str(exception), settings.LogTypes.error)
        settings.current_stage = 'Stopped! Exception Raised!'



class MyLabel(Label):
    pass


class MyH1Label(MyLabel):
    pass


class MyH2Label(MyLabel):
    pass


class MyButton(Button):
    pass


class MyLogLabel(Label):
    def __init__(self, **kwargs):
        super(MyLogLabel, self).__init__(**kwargs)

    pass


class StartupScreen(Screen):
    trd = threading.Thread
    first_start = True
    finish_switch = True
    count = 0
    logs = Queue()

    def __init__(self, **kwargs):
        super(StartupScreen, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_settings, 0.0)
        self.ids.file_name.text = settings.GetFileName()
        self.ids.failed_file_name.text = settings.GetFailedFileName()
        self.ids.api_key.text = settings.GetAPIKey()
        self.ids.file_location.text = settings.GetFilePath()

    @mainthread
    def update_settings(self, *args):
        while not settings.log_text.empty():
            scroll = self.ids.scroll.scroll_y
            vp_height = self.ids.scroll.viewport_size[1]
            sv_height = self.ids.scroll.height
            scroll_lock = scroll == 0.0 or scroll == 1.0
            add_log = MyLogLabel(text=settings.log_text.get())
            self.ids.log_grid.add_widget(add_log)
            self.logs.put(add_log)
            if self.count >= 2000:
                self.ids.log_grid.remove_widget(self.logs.get())
            else:
                self.count += 1
            if vp_height > sv_height and not scroll_lock:
                bottom = scroll * (vp_height - sv_height)
                Clock.schedule_once(partial(self.adjust_scroll, bottom + 28), -1)
        self.ids.progress_bar.max = settings.total_funds
        self.ids.progress_bar.value = settings.funds_read
        self.ids.stage_label.text = settings.current_stage
        if ('Done!' in settings.current_stage or 'Stopped' in settings.current_stage) and self.finish_switch:
            self.trd.join()
            self.first_start = True
            self.finish_switch = False
            self.ids.cancel_button.disabled = True
            self.ids.start_button.text = 'Start'
        self.ids.runtime_label.text = 'Runtime: ' + settings.runtime
        self.ids.time_label.text = 'Time Remaining: ' + settings.time_remaining

    def adjust_scroll(self, bottom, dt):
        vp_height = self.ids.scroll.viewport_size[1]
        sv_height = self.ids.scroll.height
        self.ids.scroll.scroll_y = bottom / (vp_height - sv_height)

    def button_press(self, name):
        global is_overwrite
        global is_refresh_tickers
        if 'Start' in name or 'Resume' in name:
            settings.current_stage = 'Starting'
            settings.SetFileName(self.ids.file_name.text)
            settings.SetFailedFileName(self.ids.failed_file_name.text)
            settings.SetAPIKey(self.ids.api_key.text)
            api_caller.initializeHeaders()
            if not settings.SetFilePath(self.ids.file_location.text):
                settings.log('Invalid File Path! ' + self.ids.file_location.text)
                return
            is_overwrite = self.ids.is_overwrite.active
            is_refresh_tickers = self.ids.is_refresh.active
            settings.pause_event.clear()
            settings.exit_event.clear()
            self.ids.start_button.text = 'Pause'
            if self.first_start:
                self.trd = threading.Thread(target=processSymbols, daemon=True)
                self.trd.start()
                self.finish_switch = True
                self.first_start = False
                self.ids.cancel_button.disabled = False
        elif 'Pause' in name:
            settings.pause_event.set()
            settings.current_stage = 'Paused'
            self.ids.start_button.text = 'Resume'
        elif 'Cancel' in name:
            settings.exit_event.set()
            self.trd.join()
            self.first_start = True
            settings.current_stage = 'Stopped'
            self.ids.cancel_button.disabled = True
            self.ids.start_button.text = 'Start'


class WelcomeScreen(Screen):
    button_text = "text"

    def __init__(self, **kwargs):
        super(WelcomeScreen, self).__init__(**kwargs)
        self.ids.welcome_label.text = pyjokes.get_joke(language="en", category="all")


class TickerTrackerApp(App):
    def __init__(self, **kwargs):
        super(TickerTrackerApp, self).__init__(**kwargs)
        self.root = ScreenManager()

    def build(self):
        self.icon = r'Data\Images\icon.png'
        self.root.add_widget(WelcomeScreen(name='Welcome'))
        self.root.add_widget(StartupScreen(name='Startup'))
        return self.root

    def goToScreen(self, screen_name: str):
        self.root.switch_to(self.root.get_screen(screen_name))


if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        TickerTrackerApp().run()

    except Exception as e:
        print(e)
        input("Press enter.")
