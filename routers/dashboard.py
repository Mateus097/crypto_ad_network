from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from apps.ledger.database import get_db_connection

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard & Relatórios"])


@router.get("/summary")
async def get_dashboard_summary(publisher_id: str):
    """
    Retorna o resumo de saldo, total de impressões válidas e histórico de saques do publisher.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Buscar dados de saldo e carteira do Publisher
        cursor.execute("""
            SELECT id, email, polygon_wallet, pending_balance_usd, paid_balance_usd, status
            FROM publishers 
            WHERE id = %s;
        """, (publisher_id,))
        publisher = cursor.fetchone()

        if not publisher:
            raise HTTPException(status_code=404, detail="Publisher não encontrado")

        # 2. Contar impressões totais e válidas
        cursor.execute("""
            SELECT 
                COUNT(*) as total_impressions,
                COUNT(CASE WHEN is_valid = TRUE THEN 1 END) as valid_impressions,
                COALESCE(SUM(publisher_revenue), 0) as calculated_revenue
            FROM impression_logs
            WHERE publisher_id = %s;
        """, (publisher_id,))
        stats = cursor.fetchone()

        return {
            "status": "success",
            "data": {
                "publisher_id": publisher["id"],
                "email": publisher["email"],
                "polygon_wallet": publisher["polygon_wallet"],
                "pending_balance_usd": float(publisher["pending_balance_usd"]),
                "paid_balance_usd": float(publisher["paid_balance_usd"]),
                "total_impressions": stats["total_impressions"],
                "valid_impressions": stats["valid_impressions"],
                "total_earned_usd": float(stats["calculated_revenue"])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/payouts")
async def get_payout_history(publisher_id: str):
    """
    Retorna o histórico de transferências de USDT na rede Polygon.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, amount_usd, recipient_wallet, polygon_tx_hash, status, created_at
            FROM payout_transactions
            WHERE publisher_id = %s
            ORDER BY created_at DESC;
        """, (publisher_id,))
        payouts = cursor.fetchall()

        history = []
        for p in payouts:
            tx_hash = p["polygon_tx_hash"]
            history.append({
                "id": p["id"],
                "amount_usd": float(p["amount_usd"]),
                "recipient_wallet": p["recipient_wallet"],
                "status": p["status"],
                "polygon_tx_hash": tx_hash,
                "created_at": p["created_at"],
                "polygonscan_url": f"https://polygonscan.com/tx/{tx_hash}" if tx_hash else None
            })

        return {
            "status": "success",
            "payouts": history
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")
    finally:
        cursor.close()
        conn.close()