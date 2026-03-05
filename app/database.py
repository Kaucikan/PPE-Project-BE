from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://postgres:uJkLExNxibFDNuzO@db.cxeiiuceqamnnircdpuf.supabase.co:5432/postgres"

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},   # ⭐ VERY IMPORTANT
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()