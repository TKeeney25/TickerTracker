import os
import pathlib
from dotenv import load_dotenv
import request
import logging
import logging.handlers

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

    # TODO Add Logic for backing up the database before each run
    # TODO looks like we are going to need to use selenium :(
    request.test()
    root_logger.info('Finished')

if __name__ == "__main__":
    main()