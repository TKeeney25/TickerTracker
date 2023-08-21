from pydantic import ValidationError
import requests
import csv

from database.database_models import create_db_and_tables, put_from_csi

from request.models import CSIData

import yfinance as yf

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
                    print(repr(e)) # TODO log this.
    put_from_csi(decoded_csi_data) 

def acquire_symbols():
    read_csi_data('https://apps.csidata.com/factsheets.php?type=stock&format=csv&exchangeid=MUTUAL')
    read_csi_data('https://apps.csidata.com/factsheets.php?type=stock&format=csv&isetf=1')



if __name__ == "__main__":
    # create_db_and_tables()
    # acquire_symbols()
    data = yf.Ticker('SPY')
    #print(data.info)
    print(data)