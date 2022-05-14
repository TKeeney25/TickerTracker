import json
import os
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

    def getDescendents(self) -> {}:
        get_var = self.getVars().values()
        return_set = {}
        for var in get_var:
            if isinstance(var, Segment):
                return_set[var.api_id] = var
                return_set.update(var.getDescendents())
        return return_set

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

    def getValidFilters(self) -> set[str]:
        return set()


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

    def getValidFilters(self) -> set[str]:
        return {GREATER_THAN, LESS_THAN, EQUAL}


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

    def getValidFilters(self) -> set[str]:
        return {IN, EQUAL}


class DateSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            print(data)
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

    def getValidFilters(self) -> set[str]:
        return {GREATER_THAN, LESS_THAN, EQUAL}


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

    def getValidFilters(self) -> set[str]:
        return {GREATER_THAN, LESS_THAN, EQUAL}


class ListSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        self.list = data[api_id]

    def toCSV(self) -> []:
        if self.is_wanted:
            csv = str(self.list).replace(',', '')
            return [csv]
        return []

    def getValidFilters(self) -> set[str]:
        return {IN, EQUAL}


class ReturnSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        self.year = StringSegment('year', data, is_wanted=is_wanted)
        self.annualValue = PercentSegment('annualValue', data, is_wanted=is_wanted)

    def toCSV(self) -> []:
        if self.is_wanted:
            return [[self.year] + self.annualValue.toCSV()]
        return []


class AnnualReturnSegment(Segment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        data = data[api_id]
        returns_data = data['returns']
        self.returns = []
        for my_return in returns_data:
            self.returns.append(ReturnSegment('returns', my_return, is_wanted=is_wanted))

        returnscat_data = data['returnsCat']
        self.returnsCat = []
        for my_return in returnscat_data:
            self.returnsCat.append(ReturnSegment('returnsCat', my_return, is_wanted=is_wanted))

    def toCSV(self) -> []:
        if self.is_wanted:
            returns_csv = []
            for my_return in self.returns:
                returns_csv.append(my_return.toCSV())
            returnscat_csv = []
            for my_return in self.returns:
                returnscat_csv.append(my_return.toCSV())

            return [[[' Return '] + returns_csv + [' ReturnCat '] + returnscat_csv]]
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
        self.annualTotalReturns = AnnualReturnSegment('annualTotalReturns', data, is_wanted=True)  # TODO edge case


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


def hasHadNegativeYear(returns: AnnualReturnSegment, year_span=10) -> bool:
    current_year = date.today().year
    year_range = range(current_year - year_span, current_year)
    for single_return in returns.returns:
        if single_return.year.date in year_range:
            if single_return.annualValue.failed or single_return.annualValue.raw < 0:
                return True
    return False


# Region test
FILTER_FILE = settings.DATA_FILE + 'filters.json'
FILTER_STR = 'F_'
OR = 'OR'
AND = 'AND'
NOT = 'NOT'
EQUAL = 'EQ'
GREATER_THAN = 'GT'
LESS_THAN = 'LT'
IN = 'IN'

SUCCESS = True, []


def F_OR(arg: []) -> bool:
    return any(arg)


def F_AND(arg: []) -> bool:
    return all(arg)


def F_NOT(arg: []) -> bool:
    return not arg[0]


def F_EQ(operands: [], segments: {Segment}) -> bool:
    segment = segments[operands[0]]
    compare = operands[1]
    if isinstance(segment, IntSegment):
        return segment.value == compare
    elif isinstance(segment, FloatSegment):
        return segment.raw == compare
    elif isinstance(segment, DateSegment):
        return segment.date == datetime.strptime(compare, settings.TIME_STRING)
    elif isinstance(segment, StringSegment):
        return segment.string == compare
    raise ValueError(f'{segment} does not have a F_EQ implementation!')


def F_GT(operands: [], segments: {Segment}) -> bool:
    segment = segments[operands[0]]
    compare = operands[1]
    if isinstance(segment, IntSegment):
        return segment.value > compare
    elif isinstance(segment, FloatSegment):
        return segment.raw > compare
    elif isinstance(segment, DateSegment):
        return segment.date > datetime.strptime(compare, settings.TIME_STRING)
    raise ValueError(f'{segment} does not have a F_GT implementation!')


def F_VALID(operands: [], segments: {Segment}) -> bool:
    return not segments[operands[0]].failed


def CreateFilterFile():
    global json_filters
    json_filters = {}
    json_file = open(FILTER_FILE, "w")
    json_file.write(json.dumps(json_filters, indent=4, sort_keys=True))
    json_file.close()


CreateFilterFile() if not os.path.exists(FILTER_FILE) else None
filter_file = open(FILTER_FILE)
json_filters: dict = json.load(filter_file)
filter_file.close()

OPERATOR = 'operator'
OPERANDS = 'operands'


def passesFilter(summary: Results) -> bool:
    descendents = summary.getDescendents()
    return doFilter(json_filters[OPERATOR], json_filters[OPERANDS], descendents)


def doFilter(operator: str, operands: [], segments: {}) -> bool:
    if operator in OR + AND + NOT:
        filter_results = []
        for operand in operands:
            filter_results.append(doFilter(operand[OPERATOR], operand[OPERANDS], segments))
        return getFunc(operator)(filter_results)
    else:
        return getFunc(operator)(operands, segments)


def getFunc(operator: str):
    return globals()[FILTER_STR + operator.upper()]


if __name__ == '__main__':
    api_response = api_caller.getFundInfo('FXAIX')
    symbol_dict = json.loads(api_response.text)
    results = Results(symbol_dict)
    print(passesFilter(results))
# endregion
