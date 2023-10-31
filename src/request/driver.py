from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from request.models import MS, MSTrailingReturns

# TODO combine etf/fund logic further to reduce code reuse.

def get_star_rating(driver: WebDriver) -> Optional[int]:
    try:
        element = driver.find_element(By.CLASS_NAME, 'mdc-security-header__star-rating')
        title = element.get_attribute('title') # type: ignore
        if isinstance(title, str):
            return int(title.split(' ')[0])
        else:
            return None
    except NoSuchElementException:
        return None

def start_driver() -> WebDriver:
    options = Options()
    options.add_argument("window-size=1920,1080") # type: ignore
    return webdriver.Chrome(options)

def parse_ms_table_row(row:str, row_number:int=0) -> list[str]:
    return row.split('\n')[row_number].replace('—', '0.0').split(' ')


def get_etf(driver: WebDriver, symbol: str, ms_exchange: str, fallback_exchanges: list[str]) -> MS:
    incomplete = True
    elements = []
    while incomplete and len(fallback_exchanges):
        try:
            driver.get(f"https://www.morningstar.com/etfs/{ms_exchange}/{symbol}/performance")
            elements = driver.find_elements(By.CLASS_NAME, 'mds-tbody__sal')
            if len(elements) < 2:
                raise NoSuchElementException('Less than 2 elements were found')
            incomplete = False
        except NoSuchElementException as e:
            # TODO Log it
            print(e)
            if len(fallback_exchanges) == 0:
                raise e
            else:
                ms_exchange = fallback_exchanges.pop()
    
    if 'Total Return %' not in elements[0].text:
        other_element = elements[0]
        table_element = elements[1]
    else:
        other_element = elements[1]
        table_element = elements[0]

    has_negative_value = any(float(n) < 0 for n in parse_ms_table_row(other_element.text)[2:-1])

    trailing_returns_keys = [
        'return_1d',
        'return_1w',
        'return_1m',
        'return_3m',
        'return_ytd',
        'return_1y',
        'return_3y',
        'return_5y',
        'return_10y',
        'return_15y'
        ]
    trailing_returns_values = parse_ms_table_row(table_element.text)[4:]
    trailing_returns = MSTrailingReturns(**dict(zip(trailing_returns_keys, trailing_returns_values))) #type: ignore
    rating = get_star_rating(driver)

    new_url = driver.current_url.replace('/performance', '/quote')
    driver.get(new_url)
    yield_data = float(driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div/div[2]/div[3]/div/div/main/div/div/div[1]/section[1]/sal-components/div/sal-components-etfs-quote/div/div/div/div/div/div/div[1]/div/div[2]/ul/li[8]/div/div[2]').text.replace('%', ''))
    category_data = driver.find_element(By.XPATH, '//*[@id="__layout"]/div/div/div[2]/div[3]/div/div/main/div/div/div[1]/section[1]/sal-components/div/sal-components-etfs-quote/div/div/div/div/div/div/div[1]/div/div[2]/ul/li[12]/div/div[2]').text
    print(yield_data, category_data)
    return MS(morningstar_rating=rating, has_had_negative_return=has_negative_value, **trailing_returns.dict())
print(get_etf(start_driver(), 'qqq', 'xnas', ['xnas']))
def get_fund(driver: WebDriver, symbol: str, ms_exchange: str, fallback_exchanges: list[str]) -> MS:
    incomplete = True
    elements = []
    while incomplete and len(fallback_exchanges):
        try:
            driver.get(f"https://www.morningstar.com/funds/{ms_exchange}/{symbol}/performance")
            elements = driver.find_elements(By.CLASS_NAME, 'mds-tbody__sal')
            if len(elements) < 2:
                raise NoSuchElementException('Less than 2 elements were found')
            incomplete = False
        except NoSuchElementException as e:
            # TODO Log it
            print(e)
            if len(fallback_exchanges) == 0:
                raise e
            else:
                ms_exchange = fallback_exchanges.pop()

    
    if 'Category Name' in elements[0].text:
        other_element = elements[0]
        table_element = elements[1]
    else:
        other_element = elements[1]
        table_element = elements[0]

    has_negative_value = any(float(n) < 0 for n in parse_ms_table_row(other_element.text)[1:-1])

    trailing_returns_keys = [
        'return_1d',
        'return_1w',
        'return_1m',
        'return_3m',
        'return_ytd',
        'return_1y',
        'return_3y',
        'return_5y',
        'return_10y',
        'return_15y'
        ]
    trailing_returns_values = parse_ms_table_row(table_element.text)[1:]
    trailing_returns = MSTrailingReturns(**dict(zip(trailing_returns_keys, trailing_returns_values))) #type: ignore
    rating = get_star_rating(driver)

    return MS(morningstar_rating=rating, has_had_negative_return=has_negative_value, **trailing_returns.dict())

def get_symbol(driver: WebDriver, symbol: str, exchange: str, sub_exchange: str) -> Optional[MS]:
    exchange = exchange.lower()
    sub_exchange = sub_exchange.lower()
    try:
        if 'bats' in sub_exchange or 'toronto' in sub_exchange:
            return get_etf(driver, symbol, 'bats', ['xnas', 'arcx'])
        elif 'arca' in sub_exchange:
            return get_etf(driver, symbol, 'arcx', ['xnas', 'bats'])
        elif 'mutual' in exchange:
            return get_fund(driver, symbol, 'xnas', ['arcx', 'bats'])
        elif 'nasdaq' in exchange or ('nyse' in exchange and len(sub_exchange) == 0):
            return get_etf(driver, symbol, 'xnas', ['arcx', 'bats'])
        else:
            return get_etf(driver, symbol, 'arcx', ['xnas', 'bats'])
    except Exception as e:
        #TODO LOG
        print(e)
        return None

