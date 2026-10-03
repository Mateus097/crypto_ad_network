from fastapi import APIRouter, Request, HTTPException
from apps.adserver.anti_fraud import AntiFraudEngine
from apps.ledger.database import record_impression_and_update_balance

router = APIRouter(prefix="/api/v1/ads", tags=["AdServer"])

PLATFORM_FEE = 0.20  # 20% Plataforma / 80% Publisher


@router.get("/get-ad")
async def serve_ad(request: Request, publisher_id: str):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    # 1. Validação Antifraude básica
    if not AntiFraudEngine.is_valid_request(client_ip, user_agent):
        raise HTTPException(status_code=403, detail="Tráfego inválido detectado")

    # 2. Simulação de Requisição à Ad Exchange parceira
    dsp_response = fetch_from_dsp()
    cpm_usd = dsp_response.get("cpm_price", 1.50)

    # 3. Partilha de Receita (80/20)
    impression_revenue = cpm_usd / 1000.0
    publisher_share = impression_revenue * (1 - PLATFORM_FEE)
    platform_share = impression_revenue * PLATFORM_FEE

    # 4. Gravar no PostgreSQL local
    try:
        record_impression_and_update_balance(
            publisher_id=publisher_id,
            gross_cpm=cpm_usd,
            pub_share=publisher_share,
            plat_share=platform_share,
            ip=client_ip,
            ua=user_agent
        )
    except Exception as e:
        # Silencia ou gera log do erro do banco para não travar a exibição do banner
        print(f"[ERRO BANCO DE DADOS]: {e}")

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