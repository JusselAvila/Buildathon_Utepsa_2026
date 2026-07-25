from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agrodata-frontend-mfw4-q8ha1kio2-marcos-arnez.vercel.app"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok"}


# ---- NUEVO: modelos de datos ----

class SolicitudAlerta(BaseModel):
    lat: float
    lon: float
    fecha_siembra: date
    cultivo: str

class RespuestaAlerta(BaseModel):
    alerta: str
    fase_fenologica: str
    nivel_riesgo: str
    audio_url: str | None = None


# ---- NUEVO: funciones stub ----

def calcular_fase_fenologica(fecha_siembra: date, cultivo: str) -> str:
    dias = (date.today() - fecha_siembra).days
    if dias < 20:
        return "V (vegetativa)"
    elif dias < 45:
        return "R1 (floracion)"
    else:
        return "R5 (llenado de grano)"

def consultar_clima(lat: float, lon: float) -> dict:
    # TODO: reemplazar con API real de clima
    return {"humedad": 85, "temperatura": 26, "lluvia_mm": 40}

def generar_alerta_rag(clima: dict, fase: str, cultivo: str) -> dict:
    # TODO: reemplazar por llamada real al modulo del AI Engineer
    return {
        "texto": "[STUB] Alerta de prueba - humedad alta detectada",
        "nivel_riesgo": "medio",
        "audio_url": None
    }


# ---- NUEVO: endpoint principal ----

@app.post("/generar-alerta", response_model=RespuestaAlerta)
def generar_alerta(datos: SolicitudAlerta):
    fase = calcular_fase_fenologica(datos.fecha_siembra, datos.cultivo)
    clima = consultar_clima(datos.lat, datos.lon)
    resultado_rag = generar_alerta_rag(clima, fase, datos.cultivo)

    return RespuestaAlerta(
        alerta=resultado_rag["texto"],
        fase_fenologica=fase,
        nivel_riesgo=resultado_rag["nivel_riesgo"],
        audio_url=resultado_rag.get("audio_url")
    )
