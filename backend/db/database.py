from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from backend.db.models import Base

# Connection bootstrapping mapping securely to PostgreSQL standard dialect logic 
engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Builds database schemas forcefully onto target RDBMS mapping. Ideally replaced by Alembic locally in production"""
    Base.metadata.create_all(bind=engine)
