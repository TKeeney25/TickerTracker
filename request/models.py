from typing import Optional
from pydantic import BaseModel, Field, validator

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

class EODETF(BaseModel):
    category: str = Field(..., alias='General::Category')
    yield_data: float = Field(..., alias='ETF_Data::Yield')
    morningstar_rating: int = Field(..., alias='ETF_Data::MorningStar::Ratio')
    return_ytd: float = Field(..., alias='ETF_Data::Performance::Returns_YTD')
    return_1y: float = Field(..., alias='ETF_Data::Performance::Returns_1Y')
    return_3y: float = Field(..., alias='ETF_Data::Performance::Returns_3Y')
    return_5y: float = Field(..., alias='ETF_Data::Performance::Returns_5Y')
    return_10y: float = Field(..., alias='ETF_Data::Performance::Returns_10Y')

class EODFUND(BaseModel):
    category: str = Field(..., alias='General::Fund_Category')
    yield_data: int = Field(..., alias='MutualFund_Data::Yield')
    morningstar_rating: Optional[int] = Field(..., alias='MutualFund_Data::Morning_Star_Rating')
# General::Fund_Category,MutualFund_Data::Morning_Star_Rating,MutualFund_Data::Yield