from selenium import webdriver
from selenium.webdriver.common.by import By

def fund():
    driver = webdriver.Chrome()

    driver.get("https://www.morningstar.com/funds/xnas/FTHSX/performance")
    elements = driver.find_elements(By.CLASS_NAME, 'mds-tbody__sal')
    
    if 'Category Name' in elements[0].text:
        other_element = elements[0]
        table_element = elements[1]
    else:
        other_element = elements[1]
        table_element = elements[0]
    print(other_element.text.split('\n')[0].replace('—', '0.0').split(' ')[1:-1]) # TODO turn into own function TODO '—' is not '-'!!!!!!
    print(any(float(n) < 0 for n in other_element.text.split('\n')[0].split(' ')[1:-1])) # type: ignore

    trailing_returns = table_element.text.split('\n')[0].split(' ')[1:]
    print(trailing_returns)

    element = driver.find_element(By.CLASS_NAME, 'mdc-security-header__star-rating')
    title = element.get_attribute('title') # type: ignore
    if isinstance(title, str):
        rating = title.split(' ')[0]
        print(rating)
    input('Press any Key to Continue')
    driver.quit()

def etf():
    driver = webdriver.Chrome()

    driver.get("https://www.morningstar.com/etfs/arcx/vti/performance")
    elements = driver.find_elements(By.CLASS_NAME, 'mds-tbody__sal')
    table_element = None
    for element in elements:
        if 'Total Return % (Price)' in element.text:
            table_element = element
            break
    if table_element == None:
        raise Exception('TODO') # TODO

    trailing_returns = table_element.text.split('\n')[0].split(' ')[4:]
    print(trailing_returns)

    table_element = driver.find_element(By.CLASS_NAME, 'mdc-security-header__star-rating')
    title = table_element.get_attribute('title') # type: ignore
    if isinstance(title, str):
        rating = title.split(' ')[0]
        print(rating)
    input('Press any Key to Continue')
    driver.quit()

fund()