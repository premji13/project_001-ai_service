from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.models import Base

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
                       )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        columns = {
            column["name"]
            for column in inspect(connection).get_columns("documents")
        }
        if "user_id" in columns:
            connection.execute(text("ALTER TABLE documents DROP COLUMN user_id"))
