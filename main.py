import uuid
import logging
from datetime import date, datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
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

CULTIVOS_VALIDOS = {"soya", "trigo", "sorgo", "maiz"}
ORIGENES_VALIDOS = {"manual", "gps"}


class ParcelaCrear(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    cultivo: str
    superficie_ha: float | None = None
    lat: float
    lon: float
    origen_coords: str
    region: str | None = None
    fecha_siembra: date | None = None

    @field_validator("lat")
    @classmethod
    def validar_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("lat debe estar entre -90 y 90")
        return v

    @field_validator("lon")
    @classmethod
    def validar_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("lon debe estar entre -180 y 180")
        return v

    @field_validator("cultivo")
    @classmethod
    def validar_cultivo(cls, v):
        v = v.lower().strip()
        if v not in CULTIVOS_VALIDOS:
            raise ValueError(f"cultivo debe ser uno de: {', '.join(CULTIVOS_VALIDOS)}")
        return v

    @field_validator("origen_coords")
    @classmethod
    def validar_origen(cls, v):
        v = v.lower().strip()
        if v not in ORIGENES_VALIDOS:
            raise ValueError(f"origen_coords debe ser uno de: {', '.join(ORIGENES_VALIDOS)}")
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("nombre no puede estar vacio")
        return v.strip()


class ParcelaActualizar(BaseModel):
    nombre: str | None = None
    cultivo: str | None = None
    superficie_ha: float | None = None
    lat: float | None = None
    lon: float | None = None
    origen_coords: str | None = None
    region: str | None = None
    fecha_siembra: date | None = None

    @field_validator("lat")
    @classmethod
    def validar_lat(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError("lat debe estar entre -90 y 90")
        return v

    @field_validator("lon")
    @classmethod
    def validar_lon(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError("lon debe estar entre -180 y 180")
        return v

    @field_validator("cultivo")
    @classmethod
    def validar_cultivo(cls, v):
        if v is not None:
            v = v.lower().strip()
            if v not in CULTIVOS_VALIDOS:
                raise ValueError(f"cultivo debe ser uno de: {', '.join(CULTIVOS_VALIDOS)}")
        return v


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

    logger.info(f"Parcela creada: {nueva_parcela.id} ({nueva_parcela.nombre})")

    return nueva_parcela


@app.get("/parcelas", response_model=list[ParcelaRespuesta])
def listar_parcelas(
    usuario_id: uuid.UUID | None = None,
    cultivo: str | None = Query(None, description="Filtrar por cultivo: soya, trigo, sorgo, maiz"),
    region: str | None = Query(None, description="Filtrar por region"),
    orden: str = Query("creado_en_desc", description="creado_en_desc | creado_en_asc | nombre_asc"),
    db: Session = Depends(get_db)
):
    query = db.query(Parcela)

    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    if cultivo:
        query = query.filter(Parcela.cultivo == cultivo.lower().strip())
    if region:
        query = query.filter(Parcela.region.ilike(f"%{region}%"))

    if orden == "creado_en_asc":
        query = query.order_by(Parcela.creado_en.asc())
    elif orden == "nombre_asc":
        query = query.order_by(Parcela.nombre.asc())
    else:  # default: creado_en_desc
        query = query.order_by(Parcela.creado_en.desc())

    return query.all()


@app.get("/parcelas/{parcela_id}", response_model=ParcelaRespuesta)
def obtener_parcela(parcela_id: uuid.UUID, db: Session = Depends(get_db)):
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@app.put("/parcelas/{parcela_id}", response_model=ParcelaRespuesta)
def actualizar_parcela(parcela_id: uuid.UUID, datos: ParcelaActualizar, db: Session = Depends(get_db)):
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")

    datos_actualizar = datos.model_dump(exclude_unset=True)
    for campo, valor in datos_actualizar.items():
        setattr(parcela, campo, valor)

    db.commit()
    db.refresh(parcela)

    logger.info(f"Parcela actualizada: {parcela.id}")

    return parcela


@app.delete("/parcelas/{parcela_id}")
def borrar_parcela(parcela_id: uuid.UUID, db: Session = Depends(get_db)):
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")

    db.delete(parcela)
    db.commit()

    logger.info(f"Parcela borrada: {parcela_id}")

    return {"mensaje": "Parcela eliminada correctamente", "id": str(parcela_id)}
