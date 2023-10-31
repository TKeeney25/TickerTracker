import csv
import logging
import os
from pydantic import ValidationError
import requests
from database import put_from_csi
from request.models import *

def decode_csi_data(data:list) -> CSIData: # type: ignore
    return CSIData(
        symbol=data[1], # type: ignore
        long_name=data[2], # type: ignore
        exchange=data[3], # type: ignore
        is_active=data[4], # type: ignore
        start_date=data[5], # type: ignore
        end_date=data[6], # type: ignore
        sub_exchange=data[10] # type: ignore
            )

def read_csi_data(url:str):
    decoded_csi_data:list[CSIData] = []
    header = True
    with requests.get(url, stream=True) as response:
        reader = csv.reader(response.iter_lines(decode_unicode=True))
        for content in reader:
            if header:
                header = False
                continue
            if len(content) > 1 and content[4] == '1':
                try:
                    decoded_csi_data.append(decode_csi_data(content))
                except ValidationError as e:
                    logging.debug(repr(e))
    put_from_csi(decoded_csi_data) 

def acquire_symbols():
    read_csi_data('https://apps.csidata.com/factsheets.php?type=stock&format=csv&exchangeid=MUTUAL')
    read_csi_data('https://apps.csidata.com/factsheets.php?type=stock&format=csv&isetf=1')

def acquire_etf(symbol:str) -> Optional[EODETF]:
    payload = {
        'api_token': os.getenv('API_TOKEN'),
        'filter': 'General::Category,ETF_Data::Yield,ETF_Data::MorningStar::Ratio,ETF_Data::Performance::Returns_YTD,ETF_Data::Performance::Returns_1Y,ETF_Data::Performance::Returns_3Y,ETF_Data::Performance::Returns_5Y,ETF_Data::Performance::Returns_10Y'
    }
    with requests.get(f'https://eodhistoricaldata.com/api/fundamentals/{symbol}', params=payload) as response:
        response.raise_for_status()
        if response.status_code != 200:
            print(response.status_code)
            #TODO LOgging
            return None
        return EODETF(**response.json())

def acquire_fund(symbol:str) -> Optional[EODFUND]:
    # MutualFund_Data::Morning_Star_Rating
    payload = {
        'api_token': os.getenv('API_TOKEN'),
        'filter': 'General::Fund_Category,MutualFund_Data::Yield'
    }
    with requests.get(f'https://eodhistoricaldata.com/api/fundamentals/{symbol}', params=payload) as response:
        response.raise_for_status()
        if response.status_code != 200:
            print(response.status_code)
            #TODO logging
            return None
        return EODFUND(**response.json())

def test():
    logger = logging.getLogger(__name__)
    acquire_symbols()