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
            calls = [[-10.0, 10.0], [9.9, 13.0], [12.9, 20.0], [19.9, 60.0], [59.9]]
            for call in calls:
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
                self._do_screen(api_caller.YHFunctions.screen, offset, ScreenTypes.etf)
                self.json_load[Symbols.complete.value][Complete.section.value] = ScreenTypes.mutual_fund.value
                self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                self._saveJsonFile()
            print(ScreenTypes.mutual_fund.value)
            print(self.json_load[Symbols.complete.value][Complete.section.value])
            if ScreenTypes.mutual_fund.value in self.json_load[Symbols.complete.value][Complete.section.value]:
                calls = [[-10.0, 10.0], [9.9, 13.0], [12.9, 20.0], [19.9, 60.0], [59.9]]
                settings.current_stage = 'Screening: Mutual Funds'
                for num in range(len(calls)):
                    call = calls[num]
                    if not str(call) in self.json_load[Symbols.complete.value][Complete.subsection.value] and \
                            len(self.json_load[Symbols.complete.value][Complete.subsection.value]) != 0:
                        continue
                    settings.log('Screening Mutual funds with fund price in range: %s' % str(call))
                    if len(call) > 1:
                        offset = self.json_load[Symbols.complete.value][Complete.offset.value]
                        self._do_screen(
                            api_caller.YHFunctions.screenBetweenFundPrices, offset, ScreenTypes.mutual_fund,
                            call[0], call[1])
                        self.json_load[Symbols.complete.value][Complete.subsection.value] = str(calls[num + 1])
                        self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                        self._saveJsonFile()
                    else:
                        offset = self.json_load[Symbols.complete.value][Complete.offset.value]
                        self._do_screen(
                            api_caller.YHFunctions.screenGreaterThanFundPrices, offset, ScreenTypes.mutual_fund,
                            call[0])
                        self.json_load[Symbols.complete.value][Complete.is_complete.value] = True
                        self.json_load[Symbols.complete.value][Complete.section.value] = ''
                        self.json_load[Symbols.complete.value][Complete.subsection.value] = ''
                        self.json_load[Symbols.complete.value][Complete.offset.value] = 0
                        self._saveJsonFile()
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

    def _do_screen(self, function: api_caller.YHFunctions, offset: int, *args) -> []:
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
            my_json = (function.value(offset, MAX_CALL_SIZE, *args)[
                ScreenerEnum.finance.value][ScreenerEnum.result.value][0])
            total_funds = my_json[ScreenerEnum.total.value]
            offset += MAX_CALL_SIZE
            self._addToJson(my_json)
