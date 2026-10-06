from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Файл бази даних створиться локально
SQLALCHEMY_DATABASE_URL = "sqlite:///./smartdesk.db"

# connect_args={"check_same_thread": False} потрібен лише для SQLite у FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()