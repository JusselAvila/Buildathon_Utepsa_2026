import os
from sqlalchemy import create_engine, Column, Integer, Float, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Parcela(Base):
    __tablename__ = "parcelas"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    fecha_siembra = Column(Date, nullable=False)
    cultivo = Column(String, nullable=False)


def crear_tablas():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
