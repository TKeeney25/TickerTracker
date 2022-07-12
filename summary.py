import json
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import settings

# region Constants
# region Segment Constants
DEFAULT_FLOAT = -1.0
DEFAULT_INT = -1
DEFAULT_STRING = ''
TODAY = date.today()
DEFAULT_DATE = datetime(TODAY.year, TODAY.month, TODAY.day) + relativedelta(days=1)
ACQUIRE_FAILED = "N/A"
# endregion
# region Filter Constants
FILTER_FILE = settings.DATA_FILE + 'filters.json'
FILTER_STR = 'F_'
OR = 'OR'
AND = 'AND'
NOT = 'NOT'
EQUAL = 'EQ'
GREATER_THAN = 'GT'
LESS_THAN = 'LT'
IN = 'IN'
CUSTOM = 'CUSTOM'
VALID = 'VALID'
OPERATOR = 'operator'
OPERANDS = 'operands'
FILTER = 'filter'
FLAGS = 'flags'
FLAG = 'flag'
FLAG_FILTER = 'flag_filter'
# endregion
# endregion


# region Segments
class Segment:
    def __init__(self, api_id: str, data, is_wanted=True):
        self.api_id = api_id
        self.failed = False
        self.is_wanted = is_wanted
        self.data = {}
        try:
            self.data = data[self.api_id]
        except (KeyError, TypeError):
            pass

    def getVars(self) -> {}:
        var = vars(self).copy()
        var.pop('api_id')
        var.pop('failed')
        var.pop('is_wanted')
        var.pop('data')
        return var

    def getDescendents(self) -> {}:
        get_var = self.getVars().values()
        return_set = {}
        for var in get_var:
            if isinstance(var, Segment):
                return_set[var.api_id] = var
                return_set.update(var.getDescendents())
        return return_set

    def toCSV(self, get_all=False) -> []:
        return_list = []
        var = self.getVars()
        for value in var.values():
            return_list += value.toCSV(get_all)
        return return_list

    def getCSVTitles(self, get_all=False) -> []:
        return_list = []
        var = self.getVars()
        for value in var.values():
            return_list += value.getCSVTitles(get_all)
        return return_list

    def toDict(self, get_all=False) -> {}:
        return_dict = {}
        all_vars = self.getVars()
        for var in all_vars:
            if isinstance(all_vars[var], Segment):
                return_dict[var] = all_vars[var].toDict(get_all)
            else:
                return_dict[var] = all_vars[var]
        return return_dict


class DataSegment(Segment):
    def __init__(self, api_id: str, data=None, is_wanted=False):
        super().__init__(api_id, data, is_wanted=is_wanted)

    def getCSVTitles(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [self.api_id]
        else:
            return []

    def getValidFilters(self) -> []:
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
        except (KeyError, TypeError):
            self.failed = True
            self.raw = DEFAULT_FLOAT
            self.fmt = DEFAULT_FLOAT

    def convertToFloat(self):
        self.raw = TryConvertToFloat(self.raw)
        self.fmt = TryConvertToFloat(self.fmt)

    def checkInstance(self, arg) -> float:
        if not isinstance(arg, float):
            arg = DEFAULT_FLOAT
            self.failed = True
        return arg

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [self.fmt]
        return []

    def getValidFilters(self) -> []:
        return MATH_COMPARISONS


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
        except (KeyError, TypeError):
            self.failed = True
            self.raw = DEFAULT_FLOAT
            self.fmt = DEFAULT_FLOAT
        super().__init__(api_id, data, is_wanted=is_wanted)


class StringSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            if data is None or data[api_id] is None:
                raise TypeError
            self.string: str = str(data[api_id])
        except (KeyError, TypeError):
            self.failed = True
            self.string = DEFAULT_STRING

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            csv = self.string.replace(',', '')
            return [csv]
        return []

    def getValidFilters(self) -> []:
        return STRING_COMPARISONS

class BoolSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            if data is None or data[api_id] is None:
                raise TypeError
            self.bool: bool = bool(data[api_id])
        except (KeyError, TypeError):
            self.failed = True
            self.bool = False

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [str(self.is_wanted)]


class DateSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            if data is None or data[api_id] is None or data[api_id]['raw'] is None:
                raise TypeError
            self.date: datetime = datetime.fromtimestamp(data[api_id]['raw'])
        except (KeyError, TypeError):
            self.failed = True
            self.date = DEFAULT_DATE

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [self.date.strftime(settings.TIME_STRING)]
        return []

    def getValidFilters(self) -> []:
        return MATH_COMPARISONS


class IntSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            self.value: int = data[api_id]['raw']
        except (KeyError, TypeError):
            self.failed = True
            self.value = DEFAULT_INT

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [self.value]
        return []

    def getValidFilters(self) -> []:
        return MATH_COMPARISONS


class ListSegment(DataSegment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted)
        try:
            self.list = data[api_id]
        except (KeyError, TypeError):
            self.failed = True
            self.list = []

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            csv = str(self.list).replace(',', '')
            return [csv]
        return []

    def getValidFilters(self) -> []:
        return STRING_COMPARISONS


class ReturnSegment(Segment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted, data={})
        self.year = StringSegment('year', data, is_wanted=is_wanted)
        self.annualValue = PercentSegment('annualValue', data, is_wanted=is_wanted)

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            return [[self.year] + self.annualValue.toCSV()]
        return []


class AnnualReturnSegment(Segment):
    def __init__(self, api_id: str, data, is_wanted=False):
        super().__init__(api_id, is_wanted=is_wanted, data=data)
        self.returns = []
        self.returnsCat = []
        try:
            returns_data = self.data['returns']
            for my_return in returns_data:
                self.returns.append(ReturnSegment('returns', my_return, is_wanted=is_wanted))

            returnscat_data = self.data['returnsCat']
            for my_return in returnscat_data:
                self.returnsCat.append(ReturnSegment('returnsCat', my_return, is_wanted=is_wanted))
        except KeyError or TypeError:
            self.failed = True

    def toCSV(self, get_all=False) -> []:
        if self.is_wanted or get_all:
            returns_csv = []
            for my_return in self.returns:
                returns_csv.append(my_return.toCSV())
            returnscat_csv = []
            for my_return in self.returns:
                returnscat_csv.append(my_return.toCSV())

            return [[[' Return '] + returns_csv + [' ReturnCat '] + returnscat_csv]]
        return []

    def getCSVTitles(self, get_all=False) -> []:
        return []


class DefaultKeyStatistics(Segment):
    def __init__(self, data):
        super().__init__('defaultKeyStatistics', data)
        self.annualHoldingsTurnover = FloatSegment('annualHoldingsTurnover', self.data)
        self.enterpriseToRevenue = FloatSegment('enterpriseToRevenue', self.data)
        self.beta3Year = FloatSegment('beta3Year', self.data)
        self.profitMargins = PercentSegment('profitMargins', self.data)
        self.enterpriseToEbitda = FloatSegment('enterpriseToEbitda', self.data)
        self.morningStarOverallRating = IntSegment('morningStarOverallRating', self.data)
        self.legalType = StringSegment('legalType', self.data)
        self.fundInceptionDate = DateSegment('fundInceptionDate', self.data)


class FundProfile(Segment):
    def __init__(self, data):
        super().__init__('fundProfile', data)
        self.family = StringSegment('family', self.data)
        self.categoryName = StringSegment('categoryName', self.data)
        self.brokerages = ListSegment('brokerages', self.data)
        self.legalType = StringSegment('legalType', self.data)
        self.feesExpensesInvestment = FeesExpensesInvestment(self.data)


class FeesExpensesInvestment(Segment):
    def __init__(self, data):
        super().__init__('feesExpensesInvestment', data)
        self.twelveBOne = PercentSegment('twelveBOne', self.data)


class FundPerformance(Segment):
    def __init__(self, data):
        super().__init__('fundPerformance', data)
        self.trailingReturns = TrailingReturns(self.data)
        self.annualTotalReturns = AnnualReturnSegment('annualTotalReturns', self.data)


class TrailingReturns(Segment):
    def __init__(self, data):
        super().__init__('trailingReturns', data)
        self.ytd = PercentSegment('ytd', self.data)
        self.oneMonth = PercentSegment('oneMonth', self.data)
        self.threeMonth = PercentSegment('threeMonth', self.data)
        self.oneYear = PercentSegment('oneYear', self.data)
        self.threeYear = PercentSegment('threeYear', self.data)
        self.fiveYear = PercentSegment('fiveYear', self.data)
        self.tenYear = PercentSegment('tenYear', self.data)


class QuoteType(Segment):
    def __init__(self, data):
        super().__init__('quoteType', data)
        self.exchange = StringSegment('exchange', self.data)
        self.shortName = StringSegment('shortName', self.data)
        self.longName = StringSegment('longName', self.data)
        self.quoteType = StringSegment('quoteType', self.data)
        self.market = StringSegment('market', self.data)


class SummaryDetail(Segment):
    def __init__(self, data):
        super().__init__('summaryDetail', data)
        self.yield_data = PercentSegment('yield', self.data)


class Results(Segment):
    def __init__(self, data):
        super().__init__('main', data)
        self.data = data
        self.symbol = StringSegment('symbol', self.data, is_wanted=True)
        self.defaultKeyStatistics = DefaultKeyStatistics(self.data)
        self.fundProfile = FundProfile(self.data)
        self.fundPerformance = FundPerformance(self.data)
        self.quoteType = QuoteType(self.data)
        self.summaryDetail = SummaryDetail(self.data)


# endregion


# region Custom Logic
def F_HASHADNEGATIVEYEAR(arg, segments: {Segment}) -> bool:
    returns = segments['annualTotalReturns']
    try:
        year_span = int(arg[0])
    except ValueError:
        year_span = 10
    current_year = date.today().year
    year_range = range(current_year - year_span, current_year)
    for single_return in returns.returns:
        if single_return.year.string in year_range:
            if single_return.annualValue.failed or single_return.annualValue.raw < 0:
                return True
    return False
# endregion


# region Comparison Operations
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
        return segment.string.upper() == compare.upper()
    elif isinstance(segment, ListSegment):
        return compare == str(segment.list).replace('[', '').replace(']', '')
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


def F_LT(operands: [], segments: {Segment}) -> bool:
    segment = segments[operands[0]]
    compare = operands[1]
    if isinstance(segment, IntSegment):
        return segment.value < compare
    elif isinstance(segment, FloatSegment):
        return segment.raw < compare
    elif isinstance(segment, DateSegment):
        return segment.date < datetime.strptime(compare, settings.TIME_STRING)
    raise ValueError(f'{segment} does not have a F_LT implementation!')


def F_IN(operands: [], segments: {Segment}) -> bool:
    segment = segments[operands[0]]
    compare = operands[1]
    if isinstance(segment, StringSegment):
        return compare in segment.string or segment.string in compare
    elif isinstance(segment, ListSegment):
        return compare in str(segment.list)
    raise ValueError(f'{segment} does not have a F_LT implementation!')


def F_VALID(operands: [], segments: {Segment}) -> bool:
    segment = segments[operands[0]]
    segment.is_wanted = True
    return not segment.failed


def F_CUSTOM(operands: [], segments: {Segment}) -> bool:
    return _getFunction(operands[0])(operands[1:], segments)


LOGIC_COMPARISONS = [F_OR, F_AND, F_NOT]
STRING_COMPARISONS = [F_EQ, F_IN]
MATH_COMPARISONS = [F_EQ, F_GT, F_LT]
# endregion


def passesFilter(summary: Results) -> bool:
    json_filter = json_file[FILTER]
    if OPERATOR not in json_filter:
        return True
    return _recurseFilter(json_filter[OPERATOR], json_filter[OPERANDS], summary.getDescendents())


def getFlags(summary: Results) -> ([str], [bool]):
    return_tuple = ([], [])
    for flag in json_file[FLAGS]:
        return_tuple[0].append(flag[FLAG])
        flag_filter = flag[FLAG_FILTER]
        return_tuple[1].append(_recurseFilter(flag_filter[OPERATOR], flag_filter[OPERANDS], summary.getDescendents()))
    return return_tuple


def _recurseFilter(operator: str, operands: [], segments: {}) -> bool:
    if operator in OR + AND + NOT:
        filter_results = []
        for operand in operands:
            filter_results.append(_recurseFilter(operand[OPERATOR], operand[OPERANDS], segments))
        return _getFunction(operator)(filter_results)
    else:
        return _getFunction(operator)(operands, segments)


def _getFunction(operator: str):
    return globals()[FILTER_STR + operator.upper()]


def _createFilterFile():
    global json_file
    json_file = {
        (FILTER, {}),
        (FLAGS, [])
    }
    json_file = open(FILTER_FILE, "w")
    json_file.write(json.dumps(json_file, indent=4, sort_keys=True))
    json_file.close()


_createFilterFile() if not os.path.exists(FILTER_FILE) else None
my_file = open(FILTER_FILE)
json_file: dict = json.load(my_file)
my_file.close()
if __name__ == '__main__':
    import api_caller
    api_response = api_caller.getFundInfo('CMNIX')
    symbol_dict = json.loads(api_response.text)
    results = Results(symbol_dict)
    print(results)
    print(passesFilter(results))
    print(results.getCSVTitles(get_all=False))
    print(results.toCSV(get_all=False))
    print(results.toDict(get_all=True))
    print(getFlags(results))
    print('DONE')
