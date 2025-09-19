from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = f"{settings.database_type}://{settings.database_username}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
