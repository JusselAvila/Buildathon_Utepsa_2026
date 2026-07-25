import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LoteAgricola(Base):
    __tablename__ = "lotes_agricolas"

    id = Column(Integer, primary_key=True)
    nombre_lote = Column(String(100), nullable=False)
    superhectareas = Column(Numeric(10, 2), nullable=False)
    cultivo = Column(String(50), nullable=False)
    latitud = Column(Numeric(10, 6), nullable=False)
    longitud = Column(Numeric(10, 6), nullable=False)
    humedad_suelo = Column(Numeric(5, 2), nullable=False)
    ph_suelo = Column(Numeric(3, 1), nullable=False)
    materia_organica = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, server_default=func.now())


class ManualCultivo(Base):
    __tablename__ = "manuales_cultivos"

    id = Column(Integer, primary_key=True)
    cultivo = Column(String(50), nullable=True)
    titulo_regla = Column(String(150), nullable=True)
    texto_regla = Column(Text, nullable=True)
    fuente = Column(String(100), nullable=True)


def crear_tablas():
    # No fuerza cambios en tablas ya existentes, solo crea si faltan
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
