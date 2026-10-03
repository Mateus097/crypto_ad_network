import time
from apps.ledger.database import get_db_connection
from apps.web3_pay.polygon import PolygonPayoutEngine

MIN_PAYOUT_THRESHOLD_USD = 10.00  # Valor mínimo acumulado para disparar o saque ($10.00)

def process_batch_payouts():
    """
    1. Busca publishers elegíveis para pagamento no banco de dados.
    2. Executa a transferência USDT via Polygon.
    3. Atualiza saldos e histórico de saques no PostgreSQL.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    payout_engine = PolygonPayoutEngine()

    print("=== INICIANDO PROCESSAMENTO DE SAQUES EM LOTE (POLYGON) ===")

    try:
        # 1. Buscar publishers ativos com saldo pendente >= limite mínimo
        cursor.execute("""
            SELECT id, polygon_wallet, pending_balance_usd 
            FROM publishers 
            WHERE status = 'ACTIVE' AND pending_balance_usd >= %s
            FOR UPDATE; -- Trava as linhas para evitar processamento duplicado em paralelo
        """, (MIN_PAYOUT_THRESHOLD_USD,))

        eligible_publishers = cursor.fetchall()

        if not eligible_publishers:
            print("Nenhum publisher elegível para pagamento no momento.")
            return

        print(f"Encontrados {len(eligible_publishers)} publishers elegíveis para pagamento.\n")

        for pub in eligible_publishers:
            pub_id = pub["id"]
            wallet = pub["polygon_wallet"]
            amount = float(pub["pending_balance_usd"])

            print(f"-> Processando Publisher: {pub_id}")
            print(f"   Carteira: {wallet}")
            print(f"   Valor: ${amount:.2f} USDT")

            # Registra transação como PENDING no banco
            cursor.execute("""
                INSERT INTO payout_transactions (publisher_id, amount_usd, recipient_wallet, status)
                VALUES (%s, %s, %s, 'PROCESSING')
                RETURNING id;
            """, (pub_id, amount, wallet))
            tx_record_id = cursor.fetchone()["id"]
            conn.commit()

            try:
                # 2. Executa o pagamento na Blockchain Polygon
                tx_hash = payout_engine.send_usdt(to_address=wallet, amount_usd=amount)
                print(f"   ✅ Sucesso! Tx Hash: {tx_hash}")

                # 3. Atualiza saldos e marca transação como SUCCESS no PostgreSQL
                cursor.execute("""
                    UPDATE payout_transactions 
                    SET status = 'SUCCESS', polygon_tx_hash = %s, processed_at = CURRENT_TIMESTAMP
                    WHERE id = %s;

                    UPDATE publishers 
                    SET pending_balance_usd = pending_balance_usd - %s,
                        paid_balance_usd = paid_balance_usd + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (tx_hash, tx_record_id, amount, amount, pub_id))
                conn.commit()

            except Exception as pay_err:
                print(f"   ❌ Erro ao enviar na Polygon: {pay_err}")
                conn.rollback()

                # Marca a transação como FAILED
                cursor.execute("""
                    UPDATE payout_transactions 
                    SET status = 'FAILED', error_message = %s
                    WHERE id = %s;
                """, (str(pay_err), tx_record_id))
                conn.commit()

            # Pausa breve entre transações para não sobrecarregar a RPC / Nonce
            time.sleep(2)

    except Exception as e:
        conn.rollback()
        print(f"[ERRO GERAL DE PROCESSAMENTO]: {e}")
    finally:
        cursor.close()
        conn.close()
        print("\n=== PROCESSAMENTO CONCLUÍDO ===")

if __name__ == "__main__":
    process_batch_payouts()