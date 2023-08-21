from pydantic import BaseModel, validator

from utils.date_utils import convert_str_to_epoch_seconds

class CSIData(BaseModel):
    symbol: str
    long_name: str
    exchange: str
    is_active: int
    start_date: int
    end_date: int

    @validator('start_date', 'end_date', pre=True)
    def convert_date_to_int(cls, v: str):
        return convert_str_to_epoch_seconds(v)
    
    @validator('exchange') # TODO convert to enum validation
    def validate_exchange(cls, v: str):
        valid_exchanges = {'AMEX', 'NYSE', 'NASDAQ', 'MUTUAL'}
        if v not in valid_exchanges:
            raise ValueError('Invalid Exchange')
        return v