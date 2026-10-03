import os

# Mapeamento da estrutura de pastas e arquivos do projeto
FILES = {
    "requirements.txt": """fastapi>=0.100.0
uvicorn>=0.22.0
web3>=6.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
requests>=2.31.0
""",

    ".env.example": """# Configurações de Conexão com a Blockchain Polygon
POLYGON_RPC_URL=https://polygon-rpc.com
PLATFORM_WALLET_ADDRESS=0x0000000000000000000000000000000000000000
PLATFORM_PRIVATE_KEY=sua_chave_privada_aqui

# Configurações do Banco de Dados PostgreSQL
DATABASE_URL=postgresql://usuario:senha@localhost:5432/crypto_ad_db
""",

    ".gitignore": """.env
__pycache__/
*.pyc
.idea/
venv/
.venv/
""",

    "apps/__init__.py": "",
    "apps/adserver/__init__.py": "",
    "apps/ledger/__init__.py": "",
    "apps/web3_pay/__init__.py": "",

    "apps/adserver/anti_fraud.py": """class AntiFraudEngine:
    @staticmethod
    def is_valid_request(client_ip: str, user_agent: str) -> bool:
        \"\"\"
        Valida se a requisição de anúncio vem de um usuário humano válido.
        \"\"\"
        if not user_agent or "bot" in user_agent.lower() or "crawl" in user_agent.lower():
            return False

        # Filtro básico de IP reservado/localhost
        if client_ip in ["127.0.0.1", "localhost"]:
            return True  # Permitido para testes locais

        return True
""",

    "apps/adserver/router.py": """from fastapi import APIRouter, Request, HTTPException
from apps.adserver.anti_fraud import AntiFraudEngine

router = APIRouter(prefix="/api/v1/ads", tags=["AdServer"])

PLATFORM_FEE = 0.20  # 20% Plataforma / 80% Publisher

@router.get("/get-ad")
async def serve_ad(request: Request, publisher_id: str):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    # 1. Validação Antifraude
    if not AntiFraudEngine.is_valid_request(client_ip, user_agent):
        raise HTTPException(status_code=403, detail="Tráfego inválido detectado")

    # 2. Simulação de Requisição à Ad Exchange (DSP Agregadora)
    dsp_response = fetch_from_dsp()
    cpm_usd = dsp_response.get("cpm_price", 1.50)

    # 3. Cálculo da Partilha de Receita
    impression_revenue = cpm_usd / 1000.0
    publisher_share = impression_revenue * (1 - PLATFORM_FEE)
    platform_share = impression_revenue * PLATFORM_FEE

    # TODO: Registrar 'publisher_share' e 'platform_share' no Banco de Dados

    return {
        "status": "success",
        "ad_html": dsp_response.get("html_code"),
        "cpm_earned": publisher_share * 1000.0
    }

def fetch_from_dsp():
    return {
        "cpm_price": 2.00,
        "html_code": "<div style='border:1px solid #000;padding:10px;text-align:center;'>"
                    "<h3>Anúncio Patrocinado Web3</h3>"
                    "<p>Confira a melhor exchange do mercado!</p></div>"
    }
""",

    "apps/web3_pay/polygon.py": """import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

# Contrato Oficial USDT na Polygon Mainnet
USDT_POLYGON_ADDRESS = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

WALLET_ADDRESS = os.getenv("PLATFORM_WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PLATFORM_PRIVATE_KEY")

def execute_usdt_payout(publisher_wallet: str, amount_usd: float) -> str:
    \"\"\"
    Executa o saque na Polygon no modelo Ciclo Sincronizado.
    \"\"\"
    if not w3.is_connected():
        raise Exception("Erro ao conectar à rede Polygon")

    usdt_amount = int(amount_usd * (10 ** 6)) # 6 casas decimais
    contract = w3.eth.contract(address=USDT_POLYGON_ADDRESS, abi=ERC20_ABI)
    to_address = w3.to_checksum_address(publisher_wallet)

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.transfer(to_address, usdt_amount).build_transaction({
        'chainId': 137,
        'gas': 100000,
        'maxFeePerGas': w3.eth.gas_price,
        'maxPriorityFeePerGas': w3.to_wei('30', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return w3.to_hex(tx_hash)
""",

    "static/ad_tag.js": """(function() {
    const scriptTag = document.currentScript;
    const publisherId = scriptTag.getAttribute('data-publisher-id');
    const containerId = 'ad-container-' + Math.random().toString(36).substring(7);

    document.write('<div id="' + containerId + '">Carregando anúncio...</div>');

    fetch('http://localhost:8000/api/v1/ads/get-ad?publisher_id=' + publisherId)
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                document.getElementById(containerId).innerHTML = data.ad_html;
            }
        })
        .catch(err => console.error('Erro ao carregar anúncio:', err));
})();
""",

    "main.py": """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apps.adserver.router import router as adserver_router

app = FastAPI(
    title="Crypto Ad Network API",
    description="Rede de Anúncios Descentralizada via Polygon",
    version="1.0.0"
)

# Servir o script da Tag de Anúncios JavaScript
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir Rotas
app.include_router(adserver_router)

@app.get("/")
def health_check():
    return {"status": "online", "network": "Polygon Mainnet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"""
}


def build_project():
    for file_path, content in FILES.items():
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Criado com sucesso: {file_path}")

    print("\nToda a árvore do projeto foi gerada no seu PyCharm!")


if __name__ == "__main__":
    build_project()