import json
import enum
import os.path
from datetime import datetime
from typing import Union

# region 'Constants'
SETTINGS_FILE = 'settings.json'
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


class Settings:

    @staticmethod
    def ReCreateSettingsFile():
        global json_loaded
        json_loaded = {
            SettingTypes.api_key.value: '',
            SettingTypes.blacklist.value: [],
            SettingTypes.whitelist.value: [],
            SettingTypes.filter.value: []
        }
        Settings.SaveSettings()

    @staticmethod
    def GetAPIKey() -> str:
        return json_loaded[SettingTypes.api_key.value]

    @staticmethod
    def SetAPIKey(new_key: str, save_after=True):
        print("")
        json_loaded[SettingTypes.api_key.value] = new_key
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def AddToLog(function: str, symbol: str, error: Union[Exception, str]):
        print("Adding to log: " + function + ":" + symbol + " " + str(error))
        log_file = open("log.txt", 'a')
        log_file.write(datetime.now().strftime("%D:%H:%M:%S") + "\t" + function + "\t" + symbol + "\t" + str(error))
        log_file.close()

    @staticmethod
    def fillWhitelistFromSettings():
        global obtained_white_list
        obtained_white_list = True
        whitelist.update(json_loaded[SettingTypes.whitelist.value])

    @staticmethod
    def fillBlacklistFromSettings():
        global obtained_black_list
        obtained_black_list = True
        blacklist.update(json_loaded[SettingTypes.blacklist.value])

    @staticmethod
    def AddToWhitelist(item, save_after=True):
        print("Adding " + item + " to whitelist")
        if item not in json_loaded[SettingTypes.whitelist.value]:
            json_loaded[SettingTypes.whitelist.value].append(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def AddToBlacklist(item, save_after=True):
        print("Adding " + item + " to blacklist")
        if item not in json_loaded[SettingTypes.blacklist.value]:
            json_loaded[SettingTypes.blacklist.value].append(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def RemoveFromWhitelist(item, save_after=True):
        print("Removing " + item + " from whitelist")
        if item in json_loaded[SettingTypes.whitelist.value]:
            json_loaded[SettingTypes.whitelist.value].remove(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def RemoveFromBlacklist(item, save_after=True):
        print("Removing " + item + " from blacklist")
        if item in json_loaded[SettingTypes.blacklist.value]:
            json_loaded[SettingTypes.blacklist.value].remove(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def isInWhitelist(item):
        if not obtained_white_list:
            Settings.fillWhitelistFromSettings()
        return item.rstrip() in whitelist

    @staticmethod
    def isInBlacklist(item):
        if not obtained_black_list:
            Settings.fillBlacklistFromSettings()
        return item.rstrip() in blacklist

    @staticmethod
    def AddFilter(filter_type: MainFilters, value):
        print(filter_type.value + value)
        exit(-1)

    @staticmethod
    def RemoveFilter(filter_type: MainFilters, value):
        print(filter_type.value + value)
        exit(-1)

    @staticmethod
    def SaveSettings():
        print("Saving Settings...")
        json_file = open(SETTINGS_FILE, "w")
        json_file.write(json.dumps(json_loaded, indent=4, sort_keys=True))
        json_file.close()
        print("Settings Saved.")


# region 'Initialization'


print("Acquiring Settings...")
if not os.path.exists(SETTINGS_FILE):
    Settings.ReCreateSettingsFile()
settings_file = open(SETTINGS_FILE)
json_loaded: json = json.load(settings_file)
print(json_loaded)
print("Settings Acquired!")
settings_file.close()
# endregion
