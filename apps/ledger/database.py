import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


def get_db_connection():
    """
    Obtém uma conexão síncrona com o banco de dados PostgreSQL.
    """
    db_url = os.getenv("DATABASE_URL")

    # Fallback de segurança caso o .env não carregue
    if not db_url:
        db_url = "postgresql://postgres:123456@localhost:5432/crypto_ad_db"

    return psycopg2.connect(
        db_url,
        cursor_factory=RealDictCursor
    )


def record_impression_and_update_balance(publisher_id: str, ad_id: str, user_ip: str, user_agent: str,
                                         cpm_rate: float = 0.002):
    """
    Registra a impressão no banco e atualiza o saldo pendente do publisher.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Registrar o log de impressão
        cursor.execute("""
            INSERT INTO impression_logs (publisher_id, ad_id, user_ip, user_agent, publisher_revenue, is_valid)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id;
        """, (publisher_id, ad_id, user_ip, user_agent, cpm_rate))

        log_entry = cursor.fetchone()

        # 2. Atualizar o saldo pendente (pending_balance_usd) do publisher
        cursor.execute("""
            UPDATE publishers
            SET pending_balance_usd = pending_balance_usd + %s
            WHERE id = %s;
        """, (cpm_rate, publisher_id))

        conn.commit()
        return log_entry["id"]

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()