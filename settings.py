import json
import enum
import os.path
import traceback
from datetime import datetime, date

# region 'Constants'

SETTINGS_FILE = 'settings.json'
TIME_BOMB_FILE = 'time_bombs.json'
TIME_STRING = '%Y-%m-%d'


# endregion

# region 'Enums'


class SettingTypes(enum.Enum):
    blacklist = "Blacklist"
    whitelist = "Whitelist"
    filter = "Filters"
    api_key = "APIKey"


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


class LogTypes(enum.Enum):
    error = 'Error:'
    debug = 'Debug:'


def ReCreateSettingsFile():
    global json_loaded
    json_loaded = {
        SettingTypes.api_key.value: '',
        SettingTypes.blacklist.value: [],
        SettingTypes.whitelist.value: [],
        SettingTypes.filter.value: []
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
    print("")
    json_loaded[SettingTypes.api_key.value] = new_key
    if save_after:
        SaveSettings()


def AddToLog(function: str, symbol: str, log_type: LogTypes, message=''):
    while len(function) < 20:
        function += ' '
    while len(symbol) < 5:
        symbol += ' '
    print("Adding to log: " + str(log_type.value) + function + symbol + ' ' + message)
    log_file = open("log.txt", 'a')
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
    whitelist.update(json_loaded[SettingTypes.whitelist.value])


def fillBlacklistFromSettings():
    global obtained_black_list
    obtained_black_list = True
    for dictionary in json_loaded['FilterSets'][0][SettingTypes.blacklist.value]:
        if 'eq' in dictionary['operator']:
            blacklist.update(dictionary['operands'])
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


print("Acquiring Settings...")
if not os.path.exists(SETTINGS_FILE):
    ReCreateSettingsFile()
if not os.path.exists(TIME_BOMB_FILE):
    CreateTimebombFile()
settings_file = open(SETTINGS_FILE)
time_bomb_file = open(TIME_BOMB_FILE)
json_loaded: json = json.load(settings_file)
json_time_bombs: json = json.load(time_bomb_file)
print(json_loaded)
print("Settings Acquired!")
settings_file.close()
time_bomb_file.close()
# endregion
