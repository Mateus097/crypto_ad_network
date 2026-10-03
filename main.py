from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Importações internas do projeto
from database import engine, Base
import models
from routers import auth, adserver, dashboard

# 1. Cria todas as tabelas no PostgreSQL da nuvem automaticamente ao iniciar o servidor
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Crypto Ad Network API",
    description="API para Rede de Anúncios Web3/Crypto com pagamentos em stablecoins",
    version="1.0.0"
)

# 2. Configuração de CORS (Permite que sites externos consumam a ad_tag.js e o Painel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Servir arquivos estáticos (ad_tag.js, publisher_dashboard.html, banners, etc)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 4. Inclusão das Rotas do Sistema
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
