import json
import os.path
import threading
import traceback
from datetime import datetime, date
from statics import setting_types, log_types
from pathlib import Path
from queue import Queue

# region 'Constants'
DATA_FILE = 'Data/'
SETTINGS_FILE = DATA_FILE + 'settings.json'
SYMBOL_FILE = DATA_FILE + 'symbols.json'
TIME_BOMB_FILE = DATA_FILE + 'time_bombs.json'
TIME_STRING = DATA_FILE + '%Y-%m-%d'
# endregion

# region 'Global Variables'
blacklist = set()
whitelist = set()
obtained_black_list = False
obtained_white_list = False
current_log = DATA_FILE

log_text_queue = Queue()
runtime = '0:00:00'
time_remaining = '0:00:00'
current_stage = 'Start'
total_funds = 1
funds_read = 0
exit_event = threading.Event()
pause_event = threading.Event()
# endregion


class EndExecution(Exception):
    pass


# region Logging
def log(data, log_type=log_types.debug):
    global log_text_queue
    print(data)
    log_text_queue.put('%s' % str(data))
    AddToLog('Log', data, log_type)


def AddToLog(function: str, symbol: str, log_type: log_types, message=''):
    while len(function) < 20:
        function += ' '
    while len(symbol) < 5:
        symbol += ' '
    print("Adding to log: " + str(log_type) + function + symbol + ' ' + message)
    log_file = open(current_log, 'a')
    if log_types.error == log_type:
        log_file.write("\n%s%s\t%s\t%s\t%s" %
                       (log_type, datetime.now().strftime("%D:%H:%M:%S"), function, symbol,
                        traceback.format_exc()))
    else:
        log_file.write("\n%s%s\t%s\t%s\t%s" %
                       (log_type, datetime.now().strftime("%D:%H:%M:%S"), function, symbol, message))
    log_file.close()
# endregion


# region Settings
def CreateRepairSettingsFile():
    global json_loaded
    if json_loaded is None:
        json_loaded = {}
    key_values = [(setting_types.api_key, ''),
                  (setting_types.debug_mode, False),
                  (setting_types.file_path, os.getcwd() + '\\Results'),
                  (setting_types.file_name, 'tickers.csv'),
                  (setting_types.failed_file_name, 'failedTickers.csv'),
                  (setting_types.filters, {setting_types.whitelist: [], setting_types.blacklist: []})
                  ]
    for key_value in key_values:
        if key_value[0] not in json_loaded:
            json_loaded[key_value[0]] = key_value[1]
    SaveSettings()


def GetAPIKey() -> str:
    return json_loaded[setting_types.api_key]


def SetAPIKey(new_key: str, save_after=True):
    json_loaded[setting_types.api_key] = new_key
    print(new_key)
    if save_after:
        SaveSettings()


def GetFilePath() -> str:
    if not Path.is_dir(Path(json_loaded[setting_types.file_path])) \
            or len(json_loaded[setting_types.file_path]) == 0:
        json_loaded[setting_types.file_path] = os.getcwd() + '\\Results'
    return json_loaded[setting_types.file_path]


def SetFilePath(path_str: str, save_after=True) -> bool:
    json_loaded[setting_types.file_path] = path_str
    if save_after:
        SaveSettings()
    return Path.is_dir(Path(json_loaded[setting_types.file_path]))


def GetFileName() -> str:
    if '.csv' not in json_loaded[setting_types.file_name]:
        json_loaded[setting_types.file_name] = json_loaded[setting_types.file_name].split('.')[0] + '.csv'
    return json_loaded[setting_types.file_name]


def SetFileName(input_str: str, save_after=True):
    json_loaded[setting_types.file_name] = input_str
    if save_after:
        SaveSettings()


def GetFailedFileName() -> str:
    if '.csv' not in json_loaded[setting_types.failed_file_name]:
        json_loaded[setting_types.failed_file_name] \
            = json_loaded[setting_types.failed_file_name].split('.')[0] + '.csv'
    return json_loaded[setting_types.failed_file_name]


def SetFailedFileName(input_str: str):
    json_loaded[setting_types.failed_file_name] = input_str


def fillWhitelistFromSettings():
    global obtained_white_list
    obtained_white_list = True
    whitelist.update(set(json_loaded[setting_types.filters][setting_types.whitelist]))


def fillBlacklistFromSettings():
    global obtained_black_list
    obtained_black_list = True
    blacklist.update(set(json_loaded[setting_types.filters][setting_types.blacklist]))
    blacklist.update(set(GetFilteredTimeBombs()))


def AddToWhitelist(item, save_after=True):
    print("Adding " + item + " to whitelist")
    if item not in json_loaded[setting_types.whitelist]:
        json_loaded[setting_types.whitelist].append(item)
    if save_after:
        SaveSettings()


def AddToBlacklist(item, save_after=True):
    print("Adding " + item + " to blacklist")
    if item not in json_loaded[setting_types.blacklist]:
        json_loaded[setting_types.blacklist].append(item)
    if save_after:
        SaveSettings()


def RemoveFromWhitelist(item, save_after=True):
    print("Removing " + item + " from whitelist")
    if item in json_loaded[setting_types.whitelist]:
        json_loaded[setting_types.whitelist].remove(item)
    if save_after:
        SaveSettings()


def RemoveFromBlacklist(item, save_after=True):
    print("Removing " + item + " from blacklist")
    if item in json_loaded[setting_types.blacklist]:
        json_loaded[setting_types.blacklist].remove(item)
    if save_after:
        SaveSettings()


def isInWhitelist(item):
    if not obtained_white_list:
        fillWhitelistFromSettings()
    return item.rstrip() in whitelist


def isInBlacklist(item):
    if not obtained_black_list:
        fillBlacklistFromSettings()
    return item.rstrip() in blacklist


def AddFilter(filter_type, value):
    print(filter_type + value)
    raise NotImplemented


def RemoveFilter(filter_type, value):
    print(filter_type + value)
    raise NotImplemented


def SaveSettings():
    print("Saving Settings...")
    json_file = open(SETTINGS_FILE, "w")
    json_file.write(json.dumps(json_loaded, indent=4, sort_keys=True))
    json_file.close()
    print("Settings Saved.")
# endregion


# region Time bombs
def CreateTimebombFile():
    global json_time_bombs
    json_time_bombs = {
        "bombs": {}
    }
    SaveBombs()


def GetFilteredTimeBombs() -> list[str]:
    return_list = []
    remove_list = []
    time_bombs = GetTimeBombs()
    today = date.today()
    for bomb in time_bombs:
        if datetime.strptime(time_bombs[bomb], TIME_STRING) > datetime(today.year, today.month, today.day):
            return_list.append(bomb)
        else:
            remove_list.append(bomb)
    for bomb in remove_list:
        print(bomb + " now has ten years!")
        RemoveTimeBomb(bomb)
    return return_list


def AddTimeBomb(symbol: str, expiration: str):
    """Adds a symbol to a do-not-query list that expires on the given date"""

    json_time_bombs['bombs'][symbol] = expiration
    print("Adding bomb " + symbol + " " + expiration)
    SaveBombs()


def RemoveTimeBomb(symbol) -> str:
    removed_bomb = json_time_bombs['bombs'].pop(symbol)
    SaveBombs()
    return removed_bomb


def GetTimeBombs() -> {}:
    return json_time_bombs['bombs']


def SaveBombs():
    print("Saving Bombs...")
    json_file = open(TIME_BOMB_FILE, "w")
    json_file.write(json.dumps(json_time_bombs, indent=4, sort_keys=True))
    json_file.close()
    print("Bombs Saved.")
# endregion


# region Utilities
def MakeDirectory(directory: str):
    try:
        os.mkdir(os.getcwd() + directory)
    except OSError:
        pass


def ClearLogs():
    for file in os.listdir(DATA_FILE):
        if 'log' in file:
            if datetime.now().strftime("%d_%m_%y") not in file:
                os.remove(DATA_FILE + '/' + file)
# endregion


# region Initialization
    # region File Creation
json_loaded = None
json_time_bombs = None
MakeDirectory(r'\Data')
MakeDirectory(r'\Results')
CreateRepairSettingsFile() if not os.path.exists(SETTINGS_FILE) else None
CreateTimebombFile() if not os.path.exists(TIME_BOMB_FILE) else None
current_log += 'log_' + datetime.now().strftime("%d_%m_%y_%H%M%S") + '.txt'
    # endregion
    # region Data Loading
settings_file = open(SETTINGS_FILE)
time_bomb_file = open(TIME_BOMB_FILE)
json_loaded = json.load(settings_file)
json_time_bombs = json.load(time_bomb_file)
    # endregion
    # region Data Repair/Update
CreateRepairSettingsFile()
ClearLogs()
    # endregion
settings_file.close()
time_bomb_file.close()
# endregion
