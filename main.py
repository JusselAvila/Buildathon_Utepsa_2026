from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
