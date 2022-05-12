import json
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

import api_caller
import settings

DEFAULT_FLOAT = -1.0
DEFAULT_INT = -1
DEFAULT_STRING = ''
TODAY = date.today()
DEFAULT_DATE = datetime(TODAY.year, TODAY.month, TODAY.day) + relativedelta(days=1)


class Segment:
    def __init__(self, api_id: str, is_wanted=True):
        self.api_id = api_id
        self.failed = False
        self.is_wanted = is_wanted

    def getVars(self) -> {}:
        var = vars(self).copy()
        var.pop('api_id')
        var.pop('failed')
        var.pop('is_wanted')
        return var

    def toCSV(self) -> []:
        if not self.is_wanted:
            return []
        return_list = []
        var = self.getVars()
        for value in var.values():
            return_list += value.toCSV()
        return return_list

    def getCSVTitles(self) -> []:
        if not self.is_wanted:
            return []
        return_list = []
        var = self.getVars()
        for value in var.values():
            return_list += value.getCSVTitles()
        return return_list


class DataSegment(Segment):
    def __init__(self, api_id: str, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)

    def getCSVTitles(self) -> []:
        if self.is_wanted:
            return [self.api_id]
        else:
            return []


class FloatSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            self.raw = data[api_id]['raw']
            self.fmt = data[api_id]['fmt']
            self.convertToFloat()
            self.raw = self.checkInstance(self.raw)
            self.fmt = self.checkInstance(self.fmt)
        except KeyError:
            self.failed = True
            self.raw = DEFAULT_FLOAT
            self.fmt = DEFAULT_FLOAT

    def convertToFloat(self):
        self.raw = TryConvertToFloat(self.raw)
        self.fmt = TryConvertToFloat(self.fmt)

    def checkInstance(self, arg) -> float:
        if not isinstance(arg, float):
            arg = 0.0
            self.failed = True
        return arg

    def toCSV(self) -> []:
        if self.is_wanted:
            return [self.fmt]
        return []


def TryConvertToFloat(arg):
    try:
        arg = float(arg)
    except ValueError:
        pass
    return arg


class PercentSegment(FloatSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        try:
            data[api_id]['raw'] *= 100
            data[api_id]['fmt'] = data[api_id]['fmt'].replace('%', '')
        except KeyError:
            self.failed = True
            self.raw = DEFAULT_FLOAT
            self.fmt = DEFAULT_FLOAT
        super().__init__(api_id, data, is_wanted=is_wanted)


class StringSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            if data[api_id] is None:
                raise KeyError
            self.string: str = str(data[api_id])
        except KeyError:
            self.failed = True
            self.string = DEFAULT_STRING

    def toCSV(self) -> []:
        if self.is_wanted:
            csv = self.string.replace(',', '')
            return [csv]
        return []


class DateSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            if datetime.fromtimestamp(data[api_id]['raw']) is None:
                raise KeyError
            self.date: datetime = datetime.fromtimestamp(data[api_id]['raw'])
        except KeyError:
            self.failed = True
            self.date = DEFAULT_DATE

    def toCSV(self) -> []:
        if self.is_wanted:
            return [self.date.strftime(settings.TIME_STRING)]
        return []


class IntSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            self.value: int = data[api_id]['raw']
        except KeyError:
            self.failed = True
            self.value = DEFAULT_INT

    def toCSV(self) -> []:
        if self.is_wanted:
            return [self.value]
        return []


class ListSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        self.list = data[api_id]

    def toCSV(self) -> []:
        if self.is_wanted:
            csv = str(self.list).replace(',', '')
            return [csv]
        return []


class DefaultKeyStatistics(Segment):
    def __init__(self, data):
        super().__init__('defaultKeyStatistics')
        data = data[self.api_id]
        self.annualHoldingsTurnover = FloatSegment('annualHoldingsTurnover', data)
        self.enterpriseToRevenue = FloatSegment('enterpriseToRevenue', data)
        self.beta3Year = FloatSegment('beta3Year', data)
        self.profitMargins = PercentSegment('profitMargins', data)
        self.enterpriseToEbitda = FloatSegment('enterpriseToEbitda', data)
        self.morningStarOverallRating = IntSegment('morningStarOverallRating', data, is_wanted=True)
        self.legalType = StringSegment('legalType', data, is_wanted=True)
        self.fundInceptionDate = DateSegment('fundInceptionDate', data, is_wanted=True)


class FundProfile(Segment):
    def __init__(self, data):
        super().__init__('fundProfile')
        data = data[self.api_id]
        self.categoryName = StringSegment('categoryName', data, is_wanted=True)
        self.brokerages = ListSegment('brokerages', data, is_wanted=True)
        self.legalType = StringSegment('legalType', data, is_wanted=True)
        self.feesExpensesInvestment = FeesExpensesInvestment(data)


class FeesExpensesInvestment(Segment):
    def __init__(self, data):
        super().__init__('feesExpensesInvestment')
        data = data[self.api_id]
        self.twelveBOne = PercentSegment('twelveBOne', data, is_wanted=True)


class FundPerformance(Segment):
    def __init__(self, data):
        super().__init__('fundPerformance')
        data = data[self.api_id]
        self.trailingReturns = TrailingReturns(data)
        self.annualTotalReturns = StringSegment('annualTotalReturns', {}, is_wanted=True)  # TODO edge case


class TrailingReturns(Segment):
    def __init__(self, data):
        super().__init__('trailingReturns')
        data = data[self.api_id]
        self.ytd = PercentSegment('ytd', data, is_wanted=True)
        self.oneMonth = PercentSegment('oneMonth', data, is_wanted=True)
        self.oneYear = PercentSegment('oneYear', data, is_wanted=True)
        self.threeYear = PercentSegment('threeYear', data, is_wanted=True)
        self.fiveYear = PercentSegment('fiveYear', data, is_wanted=True)
        self.tenYear = PercentSegment('tenYear', data, is_wanted=True)


class QuoteType(Segment):
    def __init__(self, data):
        super().__init__('quoteType')
        data = data[self.api_id]
        self.longName = StringSegment('longName', data, is_wanted=True)


class SummaryDetail(Segment):
    def __init__(self, data):
        super().__init__('summaryDetail')
        data = data[self.api_id]
        self.yield_data = PercentSegment('yield', data, is_wanted=True)


class Results(Segment):
    def __init__(self, data):
        super().__init__('main')
        self.defaultKeyStatistics = DefaultKeyStatistics(data)
        self.fundProfile = FundProfile(data)
        self.fundPerformance = FundPerformance(data)
        self.quoteType = QuoteType(data)
        self.summaryDetail = SummaryDetail(data)

