import csv
import logging
import os
from pydantic import ValidationError
import requests
from database.database_models import put_from_csi
from request.models import *

def decode_csi_data(data:list) -> CSIData:
    return CSIData(
        symbol=data[1],
        long_name=data[2],
        exchange=data[3],
        is_active=data[4],
        start_date=data[5],
        end_date=data[6]
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

def acquire_etf(symbol:str) -> EODETF:
    payload = {
        'api_token': os.getenv('API_TOKEN'),
        'filter': 'General::Category,ETF_Data::Yield,ETF_Data::MorningStar::Ratio,ETF_Data::Performance::Returns_YTD,ETF_Data::Performance::Returns_1Y,ETF_Data::Performance::Returns_3Y,ETF_Data::Performance::Returns_5Y,ETF_Data::Performance::Returns_10Y'
    }
    with requests.get(f'https://eodhistoricaldata.com/api/fundamentals/{symbol}', params=payload) as response:
        return EODETF(**response.json())

def test():
    logger = logging.getLogger(__name__)
    etf_data = acquire_etf('QQQ')
    print(etf_data)
    logger.debug(etf_data)