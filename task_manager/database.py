from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "postgresql+psycopg://localhost/task_manager"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine
)

class DataBase(DeclarativeBase):
    pass