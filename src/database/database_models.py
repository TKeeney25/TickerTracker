from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum

class DataFetchStage(Enum):
    EOD = 0
    MS = 1
    FINISHED = 2


class MainDatabaseModel(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    long_name: str
    exchange: str
    is_active: int
    start_date: int
    end_date: int
    sub_exchange: str

    yield_data: Optional[int]
    category: Optional[str]

    morningstar_rating: Optional[int]
    return_ytd: Optional[float]
    return_1m: Optional[float]
    return_1y: Optional[float]
    return_3y: Optional[float]
    return_5y: Optional[float]
    return_10y: Optional[float]
    return_15y: Optional[float]
    has_had_negative_return: Optional[bool]

    data_fetch_stage:DataFetchStage = DataFetchStage.EOD

