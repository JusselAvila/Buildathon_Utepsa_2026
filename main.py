import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import Session
from fastapi import Depends
from database import crear_tablas, get_db, Parcela

load_dotenv()

app = FastAPI()


@app.on_event("startup")
def startup():
	crear_tablas()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agrodata-frontend-mfw4-q8ha1kio2-marcos-arnez.vercel.app"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok"}


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


def calcular_fase_fenologica(fecha_siembra: date, cultivo: str) -> str:
    dias = (date.today() - fecha_siembra).days
    if dias < 20:
        return "V (vegetativa)"
    elif dias < 45:
        return "R1 (floracion)"
    else:
        return "R5 (llenado de grano)"


def extraer_clima_total_gps(latitud, longitud):
    url = "https://api.open-meteo.com/v1/forecast"

    parametros = {
        "latitude": latitud,
        "longitude": longitud,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "uv_index_max",
            "et0_fao_evapotranspiration",
            "shortwave_radiation_sum"
        ],
        "hourly": [
            "relative_humidity_2m",
            "dew_point_2m",
            "wind_speed_10m",
            "wind_gusts_10m",
            "soil_temperature_10cm",
            "soil_moisture_10_to_28cm",
            "vapor_pressure_deficit"
        ],
        "timezone": "auto"
    }

    respuesta = requests.get(url, params=parametros, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def consultar_clima(lat: float, lon: float) -> dict:
    try:
        datos_crudos = extraer_clima_total_gps(lat, lon)

        # Promedios/valores del dia actual (indice 0) para resumen simple
        temp_max = datos_crudos["daily"]["temperature_2m_max"][0]
        temp_min = datos_crudos["daily"]["temperature_2m_min"][0]
        temperatura_promedio = (temp_max + temp_min) / 2

        lluvia_mm = datos_crudos["daily"]["precipitation_sum"][0]

        humedades = datos_crudos["hourly"]["relative_humidity_2m"][:24]
        humedad_promedio = sum(humedades) / len(humedades)

        humedad_suelo = datos_crudos["hourly"]["soil_moisture_10_to_28cm"][:24]
        humedad_suelo_promedio = sum(humedad_suelo) / len(humedad_suelo)

        return {
            "humedad": round(humedad_promedio, 1),
            "temperatura": round(temperatura_promedio, 1),
            "lluvia_mm": lluvia_mm,
            "humedad_suelo": round(humedad_suelo_promedio, 3),
            "evapotranspiracion": datos_crudos["daily"]["et0_fao_evapotranspiration"][0],
            "raw": datos_crudos  # dato completo, por si el AI Engineer lo necesita
        }
    except (requests.RequestException, KeyError, IndexError) as e:
        return {"humedad": 60, "temperatura": 25, "lluvia_mm": 0, "error": str(e)}


def generar_alerta_rag(clima: dict, fase: str, cultivo: str) -> dict:
    # TODO: reemplazar por llamada real al modulo del AI Engineer
    return {
        "texto": "[STUB] Alerta de prueba - humedad alta detectada",
        "nivel_riesgo": "medio",
        "audio_url": None
    }


@app.post("/generar-alerta", response_model=RespuestaAlerta)
def generar_alerta(datos: SolicitudAlerta, db: Session = Depends(get_db)):
    fase = calcular_fase_fenologica(datos.fecha_siembra, datos.cultivo)
    clima = consultar_clima(datos.lat, datos.lon)
    resultado_rag = generar_alerta_rag(clima, fase, datos.cultivo)

	
    nueva_parcela = Parcela(
    lat = datos.lat, lon = datos.lon, fecha_siembra = datos.fecha_siembra, cultivo = datos.cultivo    
    )

    db.add(nueva_parcela)
    db.commit()

    return RespuestaAlerta(
        alerta=resultado_rag["texto"],
        fase_fenologica=fase,
        nivel_riesgo=resultado_rag["nivel_riesgo"],
        audio_url=resultado_rag.get("audio_url")
    )
