import uuid
import logging
from datetime import date, datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import crear_tablas, get_db, Usuario, Parcela, ManualCultivo

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agroagent")

app = FastAPI(title="AgroAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restringir a la URL real del frontend cuando exista
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    crear_tablas()
    logger.info("Tablas creadas/verificadas correctamente")


# ---- Health check ----

@app.get("/health")
def health():
    return {"status": "ok", "service": "AgroAgent API"}


# ---- Auth demo ----

@app.post("/auth/demo")
def crear_sesion_demo(db: Session = Depends(get_db)):
    nuevo_usuario = Usuario(nombre="Usuario Demo")
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    logger.info(f"Sesion demo creada: {nuevo_usuario.id}")

    return {
        "usuario_id": str(nuevo_usuario.id),
        "nombre": nuevo_usuario.nombre
    }


# ---- Modelos Pydantic para Parcela ----

class ParcelaCrear(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    cultivo: str
    superficie_ha: float | None = None
    lat: float
    lon: float
    origen_coords: str  # "manual" | "gps"
    region: str | None = None
    fecha_siembra: date | None = None

class ParcelaRespuesta(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    nombre: str
    cultivo: str
    superficie_ha: float | None
    lat: float
    lon: float
    origen_coords: str
    region: str | None
    fecha_siembra: date | None
    creado_en: datetime

    class Config:
        from_attributes = True


# ---- CRUD de Parcelas ----

@app.post("/parcelas", response_model=ParcelaRespuesta)
def crear_parcela(datos: ParcelaCrear, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == datos.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nueva_parcela = Parcela(**datos.model_dump())
    db.add(nueva_parcela)
    db.commit()
    db.refresh(nueva_parcela)

    return nueva_parcela


@app.get("/parcelas", response_model=list[ParcelaRespuesta])
def listar_parcelas(usuario_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    query = db.query(Parcela)
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    return query.all()


@app.get("/parcelas/{parcela_id}", response_model=ParcelaRespuesta)
def obtener_parcela(parcela_id: uuid.UUID, db: Session = Depends(get_db)):
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela
