import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 1. Localiza a pasta raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Varre todas as pastas do projeto e adiciona ao sys.path do Python
for root, dirs, files in os.walk(BASE_DIR):
    if "database.py" in files or "auth.py" in files:
        if root not in sys.path:
            sys.path.insert(0, root)

# 3. Importa o banco de dados e modelos
try:
    from database import engine, Base
    import models
except ModuleNotFoundError:
    from ledger.database import engine, Base
    import ledger.models as models

# 4. Importa as rotas
try:
    from routers import auth, adserver, dashboard
except ModuleNotFoundError:
    import auth, adserver, dashboard

# Cria todas as tabelas no PostgreSQL do Render automaticamente no startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Crypto Ad Network API",
    description="API para Rede de Anúncios Web3/Crypto com pagamentos em stablecoins",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusão das Rotas
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
