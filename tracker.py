import json
import os
import sys
import threading
import time
from datetime import datetime, date, timedelta
from functools import partial
from queue import Queue
from typing import Union

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.resources import resource_add_path
from kivy.uix.screenmanager import Screen, ScreenManager
from requests import Response

import api_caller
import json_interpreter
import settings
import summary
import util
from csv_writer import CSVWriter
from statics import log_types
from style_class import *
from summary import Results

Window.size = (1280, 960)


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


is_overwrite = False
is_refresh_tickers = False


def processSymbols():
    global failed_tickers_csv, tickers_csv
    try:
        funds_read = 0  # Track all the funds read for displaying purposes
        settings.current_stage = 'Starting...'
        results = Results({})
        summary.passesFilter(results)
        headers = results.getCSVTitles() + summary.getFlags(results)[0]
        tickers_csv = CSVWriter(settings.GetFilePath() + '\\' + settings.GetFileName(), headers, is_overwrite)
        failed_tickers_csv = CSVWriter(settings.GetFilePath() + '\\' + settings.GetFailedFileName(), headers,
                                       is_overwrite)
        symbol_list = loadSymbols(is_refresh_tickers)['symbols']
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
                if tickers_csv.isInCSV(symbol) or failed_tickers_csv.isInCSV(symbol):
                    settings.log(symbol + ' already obtained. Skipping...')
                    continue
                api_response: Response = api_caller.getFundInfo(symbol)
                if '200' not in str(api_response):
                    settings.log('Api Response of %s for %s. Skipping...' % (api_response, symbol))
                    settings.AddToLog('processSymbols()', symbol, log_types.debug, str(api_response))
                    if '432' in str(api_response):
                        raise Exception('Out of API Calls! Stopping!')
                    if '401' in str(api_response) or '403' in str(api_response):
                        raise Exception('Incorrect API Key! Stopping!')
                    continue
                symbol_dict = json.loads(api_response.text)
                results = Results(symbol_dict)
                if summary.passesFilter(results):
                    settings.log('%s complete' % symbol)
                    tickers_csv.write(results.toCSV() + summary.getFlags(results)[1])
                else:
                    settings.log('Filtered %s' % symbol)
                    failed_tickers_csv.write(results.toCSV() + summary.getFlags(results)[1])
            except KeyError as exception:
                settings.log('%s threw error %s!' % (symbol, str(exception)), log_types.error)
                failed_tickers_csv.write(results.toCSV() + summary.getFlags(results)[1])
        settings.current_stage = 'Done!'
    except settings.EndExecution:
        settings.log('Stopped')
        settings.current_stage = 'Stopped'
    except Exception as exception:
        settings.log('Thread threw error: %s' % str(exception), log_types.error)
        settings.current_stage = 'Stopped! Exception Raised!'


class MyScreen(Screen):
    def __init__(self, **kwargs):
        super(MyScreen, self).__init__(**kwargs)

    def goToScreen(self, screen):
        TickerTrackerApp.goToScreen(screen)

    def goBack(self):
        TickerTrackerApp.goBack()

    def exit(self):
        TickerTrackerApp.exit()


class MenuScreen(MyScreen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)


class TrackerScreen(MyScreen):
    trd = threading.Thread
    first_start = True
    finish_switch = True
    count = 0
    logs = Queue()

    def __init__(self, **kwargs):
        super(TrackerScreen, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_settings, 0.0)
        self.ids.file_name.text = settings.GetFileName()
        self.ids.failed_file_name.text = settings.GetFailedFileName()
        self.ids.api_key.text = settings.GetAPIKey()
        self.ids.file_location.text = settings.GetFilePath()

    @mainthread
    def update_settings(self, *args):
        while not settings.log_text_queue.empty():
            scroll = self.ids.scroll.scroll_y
            vp_height = self.ids.scroll.viewport_size[1]
            sv_height = self.ids.scroll.height
            scroll_lock = scroll == 0.0 or scroll == 1.0
            add_log = MyLogLabel(text=settings.log_text_queue.get())
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
            self.ids.is_overwrite.active = False
            self.ids.is_refresh.active = False
            self.ids.back_button.disabled = True
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
            self.ids.back_button.disabled = False
            self.ids.start_button.text = 'Start'


class LogicTree:
    def __init__(self, node=None, depth=0):
        self.node = node
        self.children: list[LogicTree] = []
        self.size = 0
        self.depth = depth
        if node is not None:
            self.size = 1

    def changeNode(self, item):
        if self.node is None and item is not None:
            self.size += 1
        self.node = item
        if self.node is None:
            self.size -= 1

    def add(self, parent, item):
        if self.node in parent:
            self.children.append(LogicTree(item, depth=self.depth + 1))
            self.size += 1
            return True
        else:
            result = False
            for child in self.children:
                result = result or child.add(parent, item)
            if result:
                self.size += 1
            return result

    def remove(self, item):
        if self.node in item:
            result = self.node
            self.node = None
            self.children = []
            self.size = 0
            return result
        for child in self.children:
            if child.node in item:
                result = child.node
                self.children.remove(child)
                self.size -= 1
                return result
            result = child.remove(item)
            if result is not None:
                self.size -= 1
            return result
        return None

    def get(self, name):
        if self.node in name:
            return self
        else:
            for child in self.children:
                result = child.get(name)
                if result is not None:
                    return result
        return None


class FilterScreen(MyScreen):

    def __init__(self, **kwargs):
        super(FilterScreen, self).__init__(**kwargs)
        self.selectedPanFilter = None
        self.logic_tree = LogicTree()
        self.logic_filters = []
        self.current_id = 0
        logics = [
            'AND',
            'OR',
            'NOT',
            'XOR',
            '>',
            '≥',
            '<',
            '≤',
            '='
        ]
        logic_widgets = []
        for logic in logics:
            new_button = FilterButton(text=logic, on_release=self.addFilter)
            logic_widgets.append(new_button)
            self.ids[logic] = weakref.ref(new_button)
        titles = Results({}).getCSVTitles(get_all=True)
        data_widgets = []
        for title in titles:
            new_button = FilterButton(text=title, on_release=self.addFilter)
            data_widgets.append(new_button)
            self.ids[title] = weakref.ref(new_button)
        custom_widgets = [
            Spacer(),
        ]
        self.logic_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.logic_layout.bind(minimum_height=self.logic_layout.setter('height'))
        for logic_widget in logic_widgets:
            self.logic_layout.add_widget(Spacer())
            self.logic_layout.add_widget(logic_widget)
        self.data_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.data_layout.bind(minimum_height=self.data_layout.setter('height'))
        for data_widget in data_widgets:
            self.data_layout.add_widget(Spacer())
            self.data_layout.add_widget(data_widget)
        self.custom_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.custom_layout.bind(minimum_height=self.custom_layout.setter('height'))
        for custom_widget in custom_widgets:
            self.custom_layout.add_widget(Spacer())
            self.custom_layout.add_widget(custom_widget)
        self.changeFilter('Logic')

    def changeFilter(self, new_filter):
        if new_filter == 'Logic':
            self.resetFilter()
            self.resetWidgets()
            self.ids.LogicButton.disabled = True
            self.ids.filter_scroll.add_widget(self.logic_layout)
        elif new_filter == 'Data':
            self.resetFilter()
            self.resetWidgets()
            self.ids.DataButton.disabled = True
            self.ids.filter_scroll.add_widget(self.data_layout)
        elif new_filter == 'Custom':
            self.resetFilter()
            self.resetWidgets()
            self.ids.CustomButton.disabled = True
            self.ids.filter_scroll.add_widget(self.custom_layout)

    def resetWidgets(self):
        self.ids.filter_scroll.remove_widget(self.logic_layout)
        self.ids.filter_scroll.remove_widget(self.data_layout)
        self.ids.filter_scroll.remove_widget(self.custom_layout)

    def resetFilter(self):
        self.ids.LogicButton.disabled = False
        self.ids.DataButton.disabled = False
        self.ids.CustomButton.disabled = False

    def addFilter(self, button: FilterButton):
        self.current_id += 1
        print(f'id:{self.current_id}')
        filter_id = f'filter_{self.current_id}'
        new_ids = {}
        for ref in self.ids:
            current_item = getattr(self.ids, ref)
            if isinstance(current_item, FilterButton):
                if ref == button.text:
                    if self.logic_tree.size == 0:
                        self.logic_tree.changeNode(filter_id)
                        new_ids = new_ids | self.add_filter(filter_id, ref)
                    else:
                        if self.selectedPanFilter is not None:
                            self.logic_tree.add(self.selectedPanFilter, filter_id)
                            new_ids = new_ids | self.add_filter(filter_id, ref)

        self.ids = self.ids | new_ids

    def add_filter(self, filter_id, ref):
        logic = self.logic_tree.get(filter_id)
        if len(self.logic_filters) > logic.depth:
            filter_widget = self.logic_filters[logic.depth]
            node = LogicNode(filter_id, ref)
            filter_widget.add_widget(node)
            filter_widget.ids = filter_widget.ids | node.ids
        else:
            filter_widget = LogicFilter(filter_id, ref)
            self.ids.filter_pan.add_widget(filter_widget)
            self.logic_filters.append(filter_widget)
        new_ids = {}
        for ref2 in filter_widget.ids:
            current_item = getattr(filter_widget.ids, ref2)
            print(f'ref2{ref2}')
            if '+' in current_item.id:
                current_item.on_release = partial(self.selectPanFilter, current_item)
            else:
                current_item.on_release = partial(self.removeFilter, current_item)
            new_ids[ref2] = weakref.ref(current_item)
        return new_ids

    def selectPanFilter(self, button: PanFilterButton):
        for ref in self.ids:
            current_item = getattr(self.ids, ref)
            if isinstance(current_item, PanFilterButton):
                if ref == button.id:
                    if self.selectedPanFilter == button.id:
                        current_item.background_color = [1, 1, 1, 1]
                        self.selectedPanFilter = None
                    else:
                        current_item.background_color = [.1, .1, .1, 1]
                        self.selectedPanFilter = button.id
                else:
                    current_item.background_color = [1, 1, 1, 1]

    def removeFilter(self, button: PanFilterButton):
        if self.selectedPanFilter == button.id:
            self.selectedPanFilter = None
        self.logic_filters[self.logic_tree.get(button.id).depth].remove_widget(button.parent_view)
        self.logic_tree.remove(button.id)
        print(self.logic_tree.size)


Builder.load_file('pages/styles.kv')
Builder.load_file('pages/menu.kv')
Builder.load_file('pages/tracker.kv')
Builder.load_file('pages/filter.kv')


class TickerTracker(App):
    def __init__(self, **kwargs):
        super(TickerTracker, self).__init__(**kwargs)

        self.root = ScreenManager()
        self.screenStack = []

    def build(self):
        self.icon = r'Data\Images\icon.png'
        self.root.add_widget(MenuScreen(name='Menu'))
        self.root.add_widget(TrackerScreen(name='Tracker'))
        self.root.add_widget(FilterScreen(name='Filter'))

        return self.root

    def goToScreen(self, screen_name: str):
        self.root.transition.direction = 'left'
        self.screenStack.insert(0, self.root.current)
        self._goToScreen(screen_name)

    def goBack(self):
        if len(self.screenStack) > 0:
            self.root.transition.direction = 'right'
            self._goToScreen(self.screenStack.pop())

    def _goToScreen(self, screen_name: str):
        self.root.current = screen_name

    def exit(self):
        self.stop()


TickerTrackerApp = None

if __name__ == '__main__':
    try:
        import pyi_splash

        pyi_splash.close()
    except ImportError:
        pass

    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        TickerTrackerApp = TickerTracker()
        TickerTrackerApp.run()

    except Exception as e:
        print(e)
        input("Press enter.")
