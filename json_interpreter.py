import enum
import json
import time
from datetime import date

import settings
import api_caller
from api_caller import screen, ScreenTypes

# region 'Constants/Enums'
MAX_CALL_SIZE = 50


class ScreenerEnum(enum.Enum):
    finance = 'finance'
    result = 'result'
    fields = 'fields'
    total = 'total'
    quotes = 'quotes'
    symbol = 'symbol'


class Symbols(enum.Enum):
    complete = 'complete'
    date = 'date'
    symbols = 'symbols'


class Complete(enum.Enum):
    is_complete = 'is_complete'
    offset = 'offset'
    section = 'section'
    subsection = 'subsection'


# endregion


def getAllFunds() -> []:
    # Initialize json_load
    json_load = {Symbols.date.value: date.today().strftime(settings.TIME_STRING),
                 Symbols.complete.value: {Complete.is_complete.value: False,
                                          Complete.offset.value: 0,
                                          Complete.section.value: '',
                                          Complete.subsection.value: ''},
                 Symbols.symbols.value: []}

    # Check to see if the file is populated
    with open(settings.SYMBOL_FILE, "r") as json_file:
        if len(json_file.readlines()) > 0:
            json_file.seek(0)
            json_load = json.load(json_file)

    hit_skip_todo = False
    # Start Screening
    for screen_type in ScreenTypes:
        time_start = time.time()
        settings.current_stage = 'Screening: %s' % str(screen_type.value)
        settings.log('Screening: %s' % str(screen_type.value))
        if len(json_load[Symbols.complete.value][Complete.section.value]) > 0 \
                and screen_type.value not in json_load[Symbols.complete.value][Complete.section.value] \
                and not hit_skip_todo:
            continue
        if hit_skip_todo:
            offset = 0
            total_funds = 100
        else:
            offset = json_load[Symbols.complete.value][Complete.offset.value]
            total_funds = json_load[Symbols.complete.value][Complete.offset.value] + 100
        json_load[Symbols.complete.value][Complete.section.value] = screen_type.value
        hit_skip_todo = True
        if screen_type.value in ScreenTypes.etf.value:
            while offset <= total_funds:
                settings.log('Reading: %s/%s' % (str(offset), str(total_funds)))
                if settings.pause_event.is_set() or settings.exit_event.is_set():
                    settings.log('Paused')
                    pause_start = time.time()
                    while settings.pause_event.is_set() or settings.exit_event.is_set():
                        time.sleep(.1)
                        if settings.exit_event.is_set():
                            settings.log('Exiting')
                            exit(-1)
                    time_start += time.time() - pause_start
                time_diff = time.time() - time_start
                settings.runtime = str(time.strftime("%H:%M:%S", time.gmtime(time_diff)))
                if offset != 0:
                    settings.time_remaining = str(time.strftime("%H:%M:%S", time.gmtime(
                        (time_diff / offset) * (total_funds - offset))))
                settings.total_funds = total_funds
                settings.funds_read = offset
                json_load[Symbols.complete.value][Complete.offset.value] = offset
                return_list = []
                my_json = (screen(offset, MAX_CALL_SIZE, screen_type)[
                    ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                total_funds = my_json[ScreenerEnum.total.value]
                for quote in my_json[ScreenerEnum.quotes.value]:
                    print(quote)
                    if quote[ScreenerEnum.symbol.value] not in json_load[Symbols.symbols.value]:
                        return_list.append(quote[ScreenerEnum.symbol.value])
                    else:
                        print("Duplicate!")
                offset += MAX_CALL_SIZE
                json_load[Symbols.symbols.value] += return_list
                json_file = open("Data/symbols.json", "w")
                json_file.write(json.dumps(json_load, indent=4, sort_keys=True))
                json_file.close()
        else:
            min = -10
            max = 60
            max_funds = 9999
            calls = [[min, max], [59.9]]
            i = 0
            while i < len(calls):
                call = calls[i]
                settings.log('Reading Mutual Funds Between Fund Prices: %s' % str(call))
                time_start = time.time()
                if len(json_load[Symbols.complete.value][Complete.subsection.value]) > 0 \
                        and str(call) not in json_load[Symbols.complete.value][Complete.subsection.value] \
                        and not hit_skip_todo:
                    continue
                if hit_skip_todo:
                    offset = 0
                    total_funds = 100
                else:
                    offset = json_load[Symbols.complete.value][Complete.offset.value]
                    total_funds = json_load[Symbols.complete.value][Complete.offset.value] + 100
                json_load[Symbols.complete.value][Complete.subsection.value] = str(call)
                hit_skip_todo = True
                print(call)
                while offset <= total_funds:
                    settings.log('Reading: %s/%s' % (str(offset), str(total_funds)))
                    if settings.pause_event.is_set() or settings.exit_event.is_set():
                        settings.log('Paused')
                        pause_start = time.time()
                        while settings.pause_event.is_set() or settings.exit_event.is_set():
                            time.sleep(.1)
                            if settings.exit_event.is_set():
                                settings.log('Exiting')
                                exit(-1)
                        time_start += time.time() - pause_start
                    time_diff = time.time() - time_start
                    settings.runtime = str(time.strftime("%H:%M:%S", time.gmtime(time_diff)))
                    if offset != 0:
                        settings.time_remaining = str(time.strftime("%H:%M:%S", time.gmtime(
                            (time_diff / offset) * (total_funds - offset))))
                    settings.total_funds = total_funds
                    settings.funds_read = offset
                    json_load[Symbols.complete.value][Complete.offset.value] = offset
                    return_list = []
                    if len(call) > 1:
                        my_json = (
                            api_caller.screenBetweenFundPrices(offset, MAX_CALL_SIZE, screen_type, call[0], call[1])
                            [ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                    else:
                        my_json = (
                            api_caller.screenGreaterThanFundPrices(offset, MAX_CALL_SIZE, screen_type, call[0])
                            [ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                    total_funds = my_json[ScreenerEnum.total.value]
                    if total_funds > max_funds:
                        old_call = call[1]
                        call[1] = old_call / 2
                        calls.insert(i, [call[1] - .1, old_call])
                    for quote in my_json[ScreenerEnum.quotes.value]:
                        print(quote)
                        if quote[ScreenerEnum.symbol.value] not in json_load['symbols']:
                            return_list.append(quote[ScreenerEnum.symbol.value])
                        else:
                            print("Duplicate!")
                    offset += MAX_CALL_SIZE
                    json_load['symbols'] += return_list
                    json_file = open(settings.SYMBOL_FILE, "w")
                    json_file.write(json.dumps(json_load, indent=4, sort_keys=True))
                    json_file.close()
    json_load = {Symbols.complete.value: {Complete.is_complete.value: True,
                                          Complete.offset.value: 0,
                                          Complete.section.value: '',
                                          Complete.subsection.value: ''}}
    json_file = open(settings.SYMBOL_FILE, "w")
    json_file.write(json.dumps(json_load, indent=4, sort_keys=True))
    json_file.close()
    return json_load


class Funds:
    def __init__(self):
        self.json_load = {Symbols.date.value: date.today().strftime(settings.TIME_STRING),
                          Symbols.complete.value: {Complete.is_complete.value: False,
                                                   Complete.offset.value: 0,
                                                   Complete.section.value: ScreenTypes.etf.value,
                                                   Complete.subsection.value: ''},
                          Symbols.symbols.value: []}
        self.min_call = -10
        self.max_call = 60
        self.calls = [[self.min_call, self.max_call], [59.9]]

        # Check to see if the file is populated
        with open(settings.SYMBOL_FILE, "r") as json_file:
            if len(json_file.readlines()) > 0:
                json_file.seek(0)
                self.json_load = json.load(json_file)

    def getAllFunds(self) -> []:
        if not self.json_load[Symbols.complete.value][Complete.is_complete.value]:
            if ScreenTypes.etf.value in self.json_load[Symbols.complete.value][Complete.section.value]:
                settings.log('Screening: ETFs')
                settings.current_stage = 'Screening: ETFs'
                offset = self.json_load[Symbols.complete.value][Complete.offset.value]
                self._do_screen(api_caller.YHFunctions.screen, offset, ScreenTypes.etf, -1)
                self.json_load[Symbols.complete.value][Complete.section.value] = ScreenTypes.mutual_fund.value
                self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                self._saveJsonFile()
            print(ScreenTypes.mutual_fund.value)
            print(self.json_load[Symbols.complete.value][Complete.section.value])
            if ScreenTypes.mutual_fund.value in self.json_load[Symbols.complete.value][Complete.section.value]:
                settings.current_stage = 'Screening: Mutual Funds'
                num = 0
                while num < len(self.calls):
                    call = self.calls[num]
                    if len(self.json_load[Symbols.complete.value][Complete.subsection.value]) != 0 \
                            and len(self.calls) <= 2:
                        call = str(self.json_load[Symbols.complete.value][Complete.subsection.value])\
                            .strip('[]').split(",")
                        call[0] = float(call[0])
                        if len(call) == 2:
                            call[1] = float(call[1])
                            self.calls[num] = call
                            self.calls.insert(num + 1, [call[1] - .1, self.max_call])
                        else:
                            num = len(self.calls) - 1
                    settings.log('Screening Mutual funds with fund price in range: %s' % str(call))
                    if len(call) > 1:
                        offset = self.json_load[Symbols.complete.value][Complete.offset.value]
                        self._do_screen(
                            api_caller.YHFunctions.screenBetweenFundPrices, offset, ScreenTypes.mutual_fund,
                            num)
                        self.json_load[Symbols.complete.value][Complete.subsection.value] = str(self.calls[num + 1])
                        self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                        self._saveJsonFile()
                    else:
                        offset = self.json_load[Symbols.complete.value][Complete.offset.value]
                        self._do_screen(
                            api_caller.YHFunctions.screenGreaterThanFundPrices, offset, ScreenTypes.mutual_fund,
                            num)
                        self.json_load[Symbols.complete.value][Complete.is_complete.value] = True
                        self.json_load[Symbols.complete.value][Complete.section.value] = ''
                        self.json_load[Symbols.complete.value][Complete.subsection.value] = ''
                        self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                        self._saveJsonFile()
                    num += 1
        return self.json_load

    def _addToJson(self, my_json: json):
        add_list = []
        for quote in my_json[ScreenerEnum.quotes.value]:
            print(quote)
            if quote[ScreenerEnum.symbol.value] not in self.json_load[Symbols.symbols.value]:
                add_list.append(quote[ScreenerEnum.symbol.value])
        self.json_load[Symbols.symbols.value] += add_list
        self._saveJsonFile()

    def _saveJsonFile(self):
        json_file = open("Data/symbols.json", "w")
        json_file.write(json.dumps(self.json_load, indent=4, sort_keys=True))
        json_file.close()

    def _do_screen(self, function: api_caller.YHFunctions, offset: int, type, call_num=-1) -> []:
        time_start = time.time()
        total_funds = offset + 100
        while offset <= total_funds:
            settings.log('Reading: %s/%s' % (str(offset), str(total_funds)))
            if settings.pause_event.is_set() or settings.exit_event.is_set():
                settings.log('Paused')
                pause_start = time.time()
                while settings.pause_event.is_set() or settings.exit_event.is_set():
                    time.sleep(.1)
                    if settings.exit_event.is_set():
                        settings.log('Exiting')
                        exit(-1)
                time_start += time.time() - pause_start
            time_diff = time.time() - time_start
            settings.runtime = str(time.strftime("%H:%M:%S", time.gmtime(time_diff)))
            if offset != 0:
                settings.time_remaining = str(time.strftime("%H:%M:%S", time.gmtime(
                    (time_diff / offset) * (total_funds - offset))))
            settings.total_funds = total_funds
            settings.funds_read = offset
            self.json_load[Symbols.complete.value][Complete.offset.value] = offset
            if ScreenTypes.mutual_fund == type:
                call = self.calls[call_num]
                if len(call) < 2:
                    my_json = (function.value(offset, MAX_CALL_SIZE, type, call[0])[
                        ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                else:
                    my_json = (function.value(offset, MAX_CALL_SIZE, type, call[0], call[1])[
                        ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                total_funds = my_json[ScreenerEnum.total.value]
                if total_funds > 9999:
                    old_call = call[1]
                    call[1] = (old_call + call[0]) / 2
                    self.calls[call_num] = call
                    self.calls.insert(call_num + 1, [call[1] - .1, old_call])
                    settings.log('Data set too big! Now screening Mutual funds with fund price in range: %s' % str(call))
                    self.json_load[Symbols.complete.value][Complete.subsection.value] = str(call)
            else:
                my_json = (function.value(offset, MAX_CALL_SIZE, type)[
                    ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
                total_funds = my_json[ScreenerEnum.total.value]

            offset += MAX_CALL_SIZE
            self._addToJson(my_json)
