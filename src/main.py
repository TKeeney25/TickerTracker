import csv
import os
import pathlib
from dotenv import load_dotenv
import request
import logging
import logging.handlers
import database


def main():
    load_dotenv()
    pathlib.Path('logs').mkdir(exist_ok=True)

    # region Initialize Logging
    logging.basicConfig(
        filename='logs/log.log',
        filemode='a',
        encoding='utf-8',
        level=os.getenv('LOGGING_LEVEL'),
        format='%(asctime)s:%(threadName)s:%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:\t%(message)s',
        )
    root_logger = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('logs/log.log', maxBytes=1024*1024, backupCount=50, encoding='utf-8')
    handler.setFormatter(fmt=logging.Formatter('%(asctime)s:%(threadName)s:%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:\t%(message)s'))
    root_logger.addHandler(handler)
    root_logger.info('Started')
    # endregion

    # TODO delete and backup database
    # database.create_db_and_tables()
    # request.acquire_symbols()
    for symbol in database.get_valid_csi_funds():
        try:
            if symbol.exchange.upper() == 'MUTUAL':
                symbol_info = request.acquire_fund(symbol.symbol)
            else:
                symbol_info = request.acquire_etf(symbol.symbol)
        except Exception as e:
            root_logger.exception(e)
            symbol_info = None
        if symbol_info is not None:
            database.update_db(symbol.symbol, symbol_info)
        else:
            root_logger.critical(f'!!SYMBOL_DROPPED!! {symbol}')

    for symbol in database.get_todo_name_eod():
        driver = request.start_driver()
        symbol_info = request.get_symbol(driver, symbol.symbol, symbol.exchange, symbol.sub_exchange)
        if symbol_info is not None:
            database.update_db(symbol.symbol, symbol_info)
        else:
            root_logger.critical(f'!!SYMBOL_DROPPED!! {symbol}')
    
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ticker', 'name', 'category', '1m return', '1yr return', '3yr return', '5yr return', '10yr return', 'yield', 'has_had_negative_year'])
        for result in database.get_results():
            writer.writerow([result.symbol, result.long_name, result.category, result.return_ytd, result.return_1m, result.return_1y, result.return_3y, result.return_5y, result.return_5y, result.return_10y, result.yield_data, result.has_had_negative_return])
    root_logger.info('Finished')

if __name__ == "__main__":
    print(database.get_epoch_from_s(years=10))
    print(database.get_epoch_from_s(days=10))
    #main()


    
