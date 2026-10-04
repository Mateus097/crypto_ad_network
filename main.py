import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Define o caminho raiz e garante que a pasta do projeto seja encontrada
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importações limpas dos pacotes internos
from ledger.database import engine, Base
import ledger.models as models
from routers import auth, adserver, dashboard

# Cria todas as tabelas no PostgreSQL da nuvem automaticamente ao iniciar o servidor
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Crypto Ad Network API",
    description="API para Rede de Anúncios Web3/Crypto com pagamentos em stablecoins",
    version="1.0.0"
)

# Configuração de CORS (Permite que sites externos e o Painel consumam a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (ad_tag.js, publisher_dashboard.html, banners, etc)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusão das Rotas do Sistema
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(adserver.router, prefix="/api/v1/adserver", tags=["Ad Server"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Crypto Ad Network API rodando na nuvem Render!",
        "docs_url": "/docs"
    }
