from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

class MainDatabaseModel(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    performance_id: str = Field(nullable=True)
    long_name: str = Field(nullable=True)

class MetadataModel(SQLModel, table=True):
    pass

class ScreenDataModel(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    long_name: str
    exchange: Optional[str] = None
    is_active: int
    start_date: str
    end_date: str
    sub_exchange: str
    exchange_symbol: str

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)