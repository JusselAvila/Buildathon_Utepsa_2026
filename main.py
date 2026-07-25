import logging
from decimal import Decimal
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from database import crear_tablas, get_db, LoteAgricola, ManualCultivo

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agroagent")

app = FastAPI(title="AgroAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    crear_tablas()
    logger.info("Conexion a BD verificada / tablas confirmadas")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AgroAgent API"}


CULTIVOS_VALIDOS = {"soya", "trigo", "sorgo", "maiz"}


# ---- Modelos Pydantic ----

class ParcelaCrear(BaseModel):
    nombre_lote: str
    superhectareas: float
    cultivo: str
    latitud: float
    longitud: float
    humedad_suelo: float
    ph_suelo: float
    materia_organica: str | None = None

    @field_validator("latitud")
    @classmethod
    def validar_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("latitud debe estar entre -90 y 90")
        return v

    @field_validator("longitud")
    @classmethod
    def validar_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("longitud debe estar entre -180 y 180")
        return v

    @field_validator("cultivo")
    @classmethod
    def validar_cultivo(cls, v):
        v = v.lower().strip()
        if v not in CULTIVOS_VALIDOS:
            raise ValueError(f"cultivo debe ser uno de: {', '.join(CULTIVOS_VALIDOS)}")
        return v

    @field_validator("nombre_lote")
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("nombre_lote no puede estar vacio")
        return v.strip()


class ParcelaActualizar(BaseModel):
    nombre_lote: str | None = None
    superhectareas: float | None = None
    cultivo: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    humedad_suelo: float | None = None
    ph_suelo: float | None = None
    materia_organica: str | None = None


class ParcelaRespuesta(BaseModel):
    id: int
    nombre_lote: str
    superhectareas: Decimal
    cultivo: str
    latitud: Decimal
    longitud: Decimal
    humedad_suelo: Decimal
    ph_suelo: Decimal
    materia_organica: str | None
    fecha_registro: str | None = None

    class Config:
        from_attributes = True

    @field_validator("fecha_registro", mode="before")
    @classmethod
    def formatear_fecha(cls, v):
        return str(v) if v is not None else None


# ---- CRUD ----

@app.post("/parcelas", response_model=ParcelaRespuesta)
def crear_parcela(datos: ParcelaCrear, db: Session = Depends(get_db)):
    nueva = LoteAgricola(**datos.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    logger.info(f"Lote creado: {nueva.id} ({nueva.nombre_lote})")
    return nueva


@app.get("/parcelas", response_model=list[ParcelaRespuesta])
def listar_parcelas(
    cultivo: str | None = Query(None),
    orden: str = Query("fecha_desc", description="fecha_desc | fecha_asc | nombre_asc"),
    db: Session = Depends(get_db)
):
    query = db.query(LoteAgricola)

    if cultivo:
        query = query.filter(LoteAgricola.cultivo == cultivo.lower().strip())

    if orden == "fecha_asc":
        query = query.order_by(LoteAgricola.fecha_registro.asc())
    elif orden == "nombre_asc":
        query = query.order_by(LoteAgricola.nombre_lote.asc())
    else:
        query = query.order_by(LoteAgricola.fecha_registro.desc())

    return query.all()


@app.get("/parcelas/{parcela_id}", response_model=ParcelaRespuesta)
def obtener_parcela(parcela_id: int, db: Session = Depends(get_db)):
    parcela = db.query(LoteAgricola).filter(LoteAgricola.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@app.put("/parcelas/{parcela_id}", response_model=ParcelaRespuesta)
def actualizar_parcela(parcela_id: int, datos: ParcelaActualizar, db: Session = Depends(get_db)):
    parcela = db.query(LoteAgricola).filter(LoteAgricola.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(parcela, campo, valor)

    db.commit()
    db.refresh(parcela)
    return parcela


@app.delete("/parcelas/{parcela_id}")
def borrar_parcela(parcela_id: int, db: Session = Depends(get_db)):
    parcela = db.query(LoteAgricola).filter(LoteAgricola.id == parcela_id).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")

    db.delete(parcela)
    db.commit()
    return {"mensaje": "Parcela eliminada correctamente", "id": parcela_id}
