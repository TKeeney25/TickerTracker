import json
import enum
import datetime

import settings

print("Acquiring Settings...")
file = open("settings.json")
json_loaded: json = json.load(file)
print(json_loaded)
print("Settings Acquired!")
file.close()


class SettingTypes(enum.Enum):
    blacklist = "Blacklist"
    filter = "Filters"
    timebomb = "Timebomb"


class MainFilters(enum.Enum):
    x = "x"
    y = "y"


class FilterTypes(enum.Enum):
    boolean = "Boolean"


fullBlackList = set()
obtainedBlackList = False

class Settings:
    @staticmethod
    def AddToBlacklist(item, save_after=True):
        print("Adding " + item + " to blacklist")
        if item not in json_loaded[SettingTypes.blacklist.value]:
            json_loaded[SettingTypes.blacklist.value].append(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def isInFullBlacklist(item):
        if not settings.obtainedBlackList:
            Settings.fillFullBlacklistFromBlackList()
        return item.rstrip() in settings.fullBlackList

    @staticmethod
    def RemoveFromBlacklist(item, save_after=True):
        print("Removing " + item + " from blacklist")
        if item in json_loaded[SettingTypes.blacklist.value]:
            json_loaded[SettingTypes.blacklist.value].remove(item)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def isInBlacklist(item) -> bool:
        return item in json_loaded[SettingTypes.blacklist.value]

    @staticmethod
    def fillFullBlacklistFromBlackList():
        settings.obtainedBlackList = True
        settings.fullBlackList.update(json_loaded[SettingTypes.blacklist.value])
        settings.fullBlackList.update(Settings.GetFilteredTimebombs())
        print("Full Blacklist: " + str(settings.fullBlackList))

    @staticmethod
    def GetFilteredTimebombs() -> list[str]:
        return_list = []
        remove_list = []
        timebombs = Settings.GetTimebombs()
        current_year = datetime.date.today().year
        for bomb in timebombs:
            if timebombs[bomb] > current_year:
                return_list.append(bomb)
            else:
                remove_list.append(bomb)
        for bomb in remove_list:
            print(bomb + " now has ten year!")
            Settings.RemoveTimebomb(bomb)
        return return_list

    @staticmethod
    def AddFilter(filterType: MainFilters, value):
        exit(-1)

    @staticmethod
    def RemoveFilter(filterType: MainFilters, value):
        exit(-1)

    @staticmethod
    def AddTimebomb(symbol, year, save_after=True):
        json_loaded[SettingTypes.timebomb.value][symbol] = year
        print("Adding bomb " + symbol + " " + str(year))
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def RemoveTimebomb(symbol, save_after=True):
        json_loaded[SettingTypes.timebomb.value].pop(symbol)
        if save_after:
            Settings.SaveSettings()

    @staticmethod
    def GetTimebombs() -> {}:
        return json_loaded[SettingTypes.timebomb.value]

    @staticmethod
    def SaveSettings():
        print("Saving Settings...")
        json_file = open("settings.json", "w")
        json_file.write(json.dumps(json_loaded, indent=4, sort_keys=True))
        json_file.close()
        print("Settings Saved.")
