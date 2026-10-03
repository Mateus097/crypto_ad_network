import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from apps.adserver.router import router as adserver_router
from routers.dashboard import router as dashboard_router
from routers.auth import router as auth_router

app = FastAPI(
    title="Crypto Ad Network API",
    description="Plataforma de Monetização de Anúncios Web3 com Payouts via Polygon (USDT)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define o caminho absoluto correto para a pasta 'static' no Windows
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Roteadores
app.include_router(auth_router)
app.include_router(adserver_router)
app.include_router(dashboard_router)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "system": "Crypto Ad Network API",
        "version": "1.0.0",
        "blockchain": "Polygon Mainnet",
        "payout_currency": "USDT"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
