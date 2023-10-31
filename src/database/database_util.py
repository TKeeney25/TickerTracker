'''
Concept:
Create a singleton database object that can be used to access data.
Figure out how to spin up a database table with minimal SQL usage.
Consider using: https://pypi.org/project/sqlmodel/ - Pydantic/SQLAlchemy tool
Good tool: https://jsontopydantic.com/
'''
from numpy import delete
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, create_engine, select, or_, col
from sqlalchemy.sql.operators import is_


from request.models import CSIData
from database.database_models import MainDatabaseModel
from utils.date_utils import get_epoch_from_s

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
        session.add_all(fixed_entries)
        session.commit()

def clear_db():
    with Session(engine) as session:
        statement = select(MainDatabaseModel)
        results = session.exec(statement)

        session.delete(results.all())
        session.commit()

def update_db(symbol: str, data: BaseModel):
    with Session(engine) as session:
        statement = select(MainDatabaseModel).where(MainDatabaseModel.symbol == symbol)
        results = session.exec(statement)
        fund = results.one()
        for k, v in data.dict():
            fund.__setattr__(k, v)
        session.add(fund)
        session.commit

def get_valid_csi_funds() -> list[MainDatabaseModel]:
    with Session(engine) as session:
        statement = select(MainDatabaseModel).\
            where(MainDatabaseModel.start_date <= get_epoch_from_s(years=10)).\
            where(MainDatabaseModel.end_date >= get_epoch_from_s(days=10)).\
            where(MainDatabaseModel.is_active == 1)
        results = session.exec(statement)
        funds = results.all()
        return funds
    
def get_todo_name_eod() -> list[MainDatabaseModel]:
    with Session(engine) as session:
        statement = select(MainDatabaseModel).\
            where(MainDatabaseModel.start_date <= get_epoch_from_s(years=10)).\
            where(MainDatabaseModel.end_date >= get_epoch_from_s(days=10)).\
            where(MainDatabaseModel.is_active == 1).\
            where(or_(is_(MainDatabaseModel.morningstar_rating, None), col(MainDatabaseModel.morningstar_rating) >= 4)).\
            where(or_(is_(MainDatabaseModel.return_10y, None), col(MainDatabaseModel.return_10y) > 0)).\
            where(or_(is_(MainDatabaseModel.return_5y, None), col(MainDatabaseModel.return_5y) > 0)).\
            where(or_(is_(MainDatabaseModel.return_3y, None), col(MainDatabaseModel.return_3y) > 0)).\
            where(or_(is_(MainDatabaseModel.return_1y, None), col(MainDatabaseModel.return_1y) > 0)).\
            where(MainDatabaseModel.data_fetch_stage.value < 2)
        results = session.exec(statement)
        funds = results.all()
        return funds
    
def get_results() -> list[MainDatabaseModel]:
    with Session(engine) as session:
        statement = select(MainDatabaseModel).\
            where(MainDatabaseModel.start_date <= get_epoch_from_s(years=10)).\
            where(MainDatabaseModel.end_date >= get_epoch_from_s(days=10)).\
            where(MainDatabaseModel.is_active == 1).\
            where(col(MainDatabaseModel.morningstar_rating) >= 4).\
            where(col(MainDatabaseModel.return_10y) > 0).\
            where(col(MainDatabaseModel.return_5y) > 0).\
            where(col(MainDatabaseModel.return_3y) > 0).\
            where(col(MainDatabaseModel.return_1y) > 0)
        results = session.exec(statement)
        funds = results.all()
        return funds
    
def get_todo_name_ms() -> list[MainDatabaseModel]:
    pass
# NYSE -> arcx - 2492
# NASDAQ -> arcx/xnas - 654
# Mutual Fund -> xnas - 25504
# AMEX -> arcx/bats - 90

# NASDAQ / Nasdaq Global Market -> xnas
# NYSE / Nasdaq Global Market -> bats

# NYSE/NYSE -> arcx
# */BATS Global Markets -> bats
# AMEX/NYSE ARCA -> arcx
# NYSE/NYSE ARCA -> arcx
# NASDAQ / NYSE ARCA -> xnas
# NASDAQ / NYSE Mkt -> xnas
# NASDAQ / Nasdaq Capital Market -> xnas
# NYSE/Nasdaq Capital Market -> arcx
# NYSE/Nasdaq Global Market -> arcx

# NASDAQ / NYSE -> xnas



# EDGE CASES (ipb)

#AMEX/BATS -> bats
#AMEX/ARCA -> arcx

#MUTUAL -> xnas

#NASDAQ/ -> xnas
#NASDAQ/Grey -> TODO DROP
#NASDAQ/NYSE -> xnas
#NASDAQ/Nasdaq -> xnas

#NASDAQ/OTC TODO DROP

#NYSE/ -> xnas
#NYSE/BATS -> bats
#NYSE/NYSE -> arcx
#NYSE/Nasdaq -> arcx
#NYSE/Toronto -> bats

#RULES (bats, arcx, xnas)
#*/BATS Global Markets -> bats
#*/Toronto Stock Exchange -> bats
#*/NYSE ARCA -> arcx
#MUTUAL/* -> xnas
#NASDAQ/* -> xnas
#NYSE/NULL -> xnas
#NYSE/* -> arcx
