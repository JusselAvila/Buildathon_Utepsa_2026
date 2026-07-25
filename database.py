import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=True)
    nombre = Column(String, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    parcelas = relationship("Parcela", back_populates="usuario")


class Parcela(Base):
    __tablename__ = "parcelas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nombre = Column(String, nullable=False)
    cultivo = Column(String, nullable=False)  # soya | trigo | sorgo | maiz
    superficie_ha = Column(Float, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    origen_coords = Column(String, nullable=False)  # manual | gps
    region = Column(String, nullable=True)
    fecha_siembra = Column(Date, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="parcelas")


class ManualCultivo(Base):
    __tablename__ = "manuales_cultivos"

    id = Column(Integer, primary_key=True)
    cultivo = Column(String, nullable=True)
    titulo_regla = Column(String, nullable=True)
    texto_regla = Column(Text, nullable=True)
    fuente = Column(String, nullable=True)


def crear_tablas():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
