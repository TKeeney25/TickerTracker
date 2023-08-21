from sqlmodel import Field, SQLModel, Session, create_engine

from request.models import CSIData

class MainDatabaseModel(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    long_name: str
    exchange: str
    is_active: int
    start_date: int
    end_date: int
    


class MorningstarDatabaseModel(SQLModel, table=True):
    performance_id: str = Field(primary_key=True)
    symbol: str
    last_acquired: int

# class ScreenDataModel(SQLModel, table=True):
#     symbol: str = Field(primary_key=True)
#     long_name: str
#     exchange: Optional[str] = None
#     is_active: int
#     start_date: str
#     end_date: str
#     sub_exchange: str
#     exchange_symbol: str

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def put_from_csi(data: list[CSIData]):
    with Session(engine) as session:
        fixed_entries = []
        for entry in data:
            fixed_entries.append(MainDatabaseModel(**entry.dict()))
        # for entry in fixed_entries:
        #     print(entry)
        #     session.add(entry)
        #     session.commit()
        session.add_all(fixed_entries)
        session.commit()