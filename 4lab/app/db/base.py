from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings

    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    with Session(engine) as session:
        yield session
        