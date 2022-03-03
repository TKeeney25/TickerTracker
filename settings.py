import json
import enum
import os.path
import threading
import traceback
from datetime import datetime, date

# region 'Constants'
from pathlib import Path
from queue import Queue

SETTINGS_FILE = 'Data/settings.json'
SYMBOL_FILE = 'Data/symbols.json'
TIME_BOMB_FILE = 'Data/time_bombs.json'
TIME_STRING = '%Y-%m-%d'


# endregion


# region 'Enums'
class SettingTypes(enum.Enum):
    blacklist = "Blacklist"
    whitelist = "Whitelist"
    filter = "Filters"
    api_key = "APIKey"
    file_path = "FilePath"
    file_name = "FileName"
    failed_file_name = "FailedFileName"


class MainFilters(enum.Enum):
    x = "x"
    y = "y"


class FilterTypes(enum.Enum):
    boolean = "Boolean"


# endregion


# region 'Global Variables'
blacklist = set()
whitelist = set()
obtained_black_list = False
obtained_white_list = False


# endregion
class EndExecution(Exception):
    pass

class LogTypes(enum.Enum):
    error = 'Error:'
    debug = 'Debug:'


log_text = Queue()
runtime = '0:00:00'
time_remaining = '0:00:00'
current_stage = 'Start'
total_funds = 1
funds_read = 0
exit_event = threading.Event()
pause_event = threading.Event()


def log(data, log_type=LogTypes.debug):
    global log_text
    print(data)
    log_text.put('%s' % str(data))
    AddToLog('Log', data, log_type)


def CreateSettingsFile():
    global json_loaded
    json_loaded = {
        SettingTypes.api_key.value: '',
        SettingTypes.file_path.value: os.getcwd() + '\\Results',
        SettingTypes.file_name.value: 'tickers.csv',
        SettingTypes.failed_file_name.value: 'failedTickers.csv',
        SettingTypes.filter.value: {
            SettingTypes.whitelist.value: [],
            SettingTypes.blacklist.value: []
        }
    }
    SaveSettings()


def CreateTimebombFile():
    global json_time_bombs
    json_time_bombs = {
        "bombs": {}
    }
    SaveBombs()


def GetAPIKey() -> str:
    return json_loaded[SettingTypes.api_key.value]


def SetAPIKey(new_key: str, save_after=True):
    json_loaded[SettingTypes.api_key.value] = new_key
    print(new_key)
    if save_after:
        SaveSettings()


def GetFilePath() -> str:
    if not Path.is_dir(Path(json_loaded[SettingTypes.file_path.value])) \
            or len(json_loaded[SettingTypes.file_path.value]) == 0:
        json_loaded[SettingTypes.file_path.value] = os.getcwd() + '\\Results'
    return json_loaded[SettingTypes.file_path.value]


def SetFilePath(path_str: str, save_after=True) -> bool:
    json_loaded[SettingTypes.file_path.value] = path_str
    if save_after:
        SaveSettings()
    return Path.is_dir(Path(json_loaded[SettingTypes.file_path.value]))


def GetFileName() -> str:
    if '.csv' not in json_loaded[SettingTypes.file_name.value]:
        json_loaded[SettingTypes.file_name.value] = json_loaded[SettingTypes.file_name.value].split('.')[0] + '.csv'
    return json_loaded[SettingTypes.file_name.value]


def SetFileName(input_str: str, save_after=True):
    json_loaded[SettingTypes.file_name.value] = input_str
    if save_after:
        SaveSettings()


def GetFailedFileName() -> str:
    if '.csv' not in json_loaded[SettingTypes.failed_file_name.value]:
        json_loaded[SettingTypes.failed_file_name.value] \
            = json_loaded[SettingTypes.failed_file_name.value].split('.')[0] + '.csv'
    return json_loaded[SettingTypes.failed_file_name.value]


def SetFailedFileName(input_str: str):
    json_loaded[SettingTypes.failed_file_name.value] = input_str


def AddToLog(function: str, symbol: str, log_type: LogTypes, message=''):
    while len(function) < 20:
        function += ' '
    while len(symbol) < 5:
        symbol += ' '
    print("Adding to log: " + str(log_type.value) + function + symbol + ' ' + message)
    log_file = open("Data/log.txt", 'a')
    if LogTypes.error == log_type:
        log_file.write("\n%s%s\t%s\t%s\t%s" %
                       (log_type.value, datetime.now().strftime("%D:%H:%M:%S"), function, symbol,
                        traceback.format_exc()))
    else:
        log_file.write("\n%s%s\t%s\t%s\t%s" %
                       (log_type.value, datetime.now().strftime("%D:%H:%M:%S"), function, symbol, message))
    log_file.close()


def fillWhitelistFromSettings():
    global obtained_white_list
    obtained_white_list = True
    whitelist.update(set(json_loaded[SettingTypes.filter.value][SettingTypes.whitelist.value]))


def fillBlacklistFromSettings():
    global obtained_black_list
    obtained_black_list = True
    blacklist.update(set(json_loaded[SettingTypes.filter.value][SettingTypes.blacklist.value]))
    blacklist.update(set(GetFilteredTimeBombs()))


def AddToWhitelist(item, save_after=True):
    print("Adding " + item + " to whitelist")
    if item not in json_loaded[SettingTypes.whitelist.value]:
        json_loaded[SettingTypes.whitelist.value].append(item)
    if save_after:
        SaveSettings()


def AddToBlacklist(item, save_after=True):
    print("Adding " + item + " to blacklist")
    if item not in json_loaded[SettingTypes.blacklist.value]:
        json_loaded[SettingTypes.blacklist.value].append(item)
    if save_after:
        SaveSettings()


def RemoveFromWhitelist(item, save_after=True):
    print("Removing " + item + " from whitelist")
    if item in json_loaded[SettingTypes.whitelist.value]:
        json_loaded[SettingTypes.whitelist.value].remove(item)
    if save_after:
        SaveSettings()


def RemoveFromBlacklist(item, save_after=True):
    print("Removing " + item + " from blacklist")
    if item in json_loaded[SettingTypes.blacklist.value]:
        json_loaded[SettingTypes.blacklist.value].remove(item)
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


def AddFilter(filter_type: MainFilters, value):
    print(filter_type.value + value)
    exit(-1)


def RemoveFilter(filter_type: MainFilters, value):
    print(filter_type.value + value)
    exit(-1)


def SaveSettings():
    print("Saving Settings...")
    json_file = open(SETTINGS_FILE, "w")
    json_file.write(json.dumps(json_loaded, indent=4, sort_keys=True))
    json_file.close()
    print("Settings Saved.")


# region 'Time bombs'
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
    json_time_bombs['bombs'][symbol] = expiration
    print("Adding bomb " + symbol + " " + expiration)
    SaveBombs()


def RemoveTimeBomb(symbol):
    json_time_bombs['bombs'].pop(symbol)
    SaveBombs()


def GetTimeBombs() -> {}:
    return json_time_bombs['bombs']


def SaveBombs():
    print("Saving Bombs...")
    json_file = open(TIME_BOMB_FILE, "w")
    json_file.write(json.dumps(json_time_bombs, indent=4, sort_keys=True))
    json_file.close()
    print("Bombs Saved.")


# region 'Initialization'
settings_file = None
time_bomb_file = None
json_loaded: json = None
json_time_bombs: json = None


def Init():
    global settings_file
    global time_bomb_file
    global json_loaded
    global json_time_bombs
    print("Acquiring Settings...")
    try:
        os.mkdir(os.getcwd() + '\\Data')
    except OSError:
        pass
    try:
        os.mkdir(os.getcwd() + '\\Results')
    except OSError:
        pass
    if not os.path.exists(SETTINGS_FILE):
        CreateSettingsFile()
    if not os.path.exists(TIME_BOMB_FILE):
        CreateTimebombFile()
    settings_file = open(SETTINGS_FILE)
    time_bomb_file = open(TIME_BOMB_FILE)
    json_loaded = json.load(settings_file)
    json_time_bombs = json.load(time_bomb_file)
    print(json_loaded)
    print("Settings Acquired!")
    settings_file.close()
    time_bomb_file.close()


Init()
# endregion
