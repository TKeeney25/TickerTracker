from re import T
from sqlmodel import Field, SQLModel

class MainDatabaseModel(SQLModel, table=True):
    symbol: str = Field(primary_key=True)