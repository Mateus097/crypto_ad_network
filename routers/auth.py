import re
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from apps.ledger.database import get_db_connection
from apps.auth.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação de Publishers"])


# Modelos para validação dos dados que chegam
class PublisherRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    polygon_wallet: str


class PublisherLoginRequest(BaseModel):
    email: EmailStr
    password: str


def is_valid_polygon_address(address: str) -> bool:
    """Valida se o endereço da carteira inicia com 0x e tem 42 caracteres."""
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_publisher(payload: PublisherRegisterRequest):
    """
    Cadastra um novo publisher no PostgreSQL com e-mail, senha criptografada e carteira Polygon.
    """
    if not is_valid_polygon_address(payload.polygon_wallet):
        raise HTTPException(
            status_code=400,
            detail="Endereço da carteira Polygon inválido. Deve iniciar com '0x' e ter 42 caracteres."
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verificar se e-mail ou carteira já existem
        cursor.execute("""
            SELECT id FROM publishers 
            WHERE email = %s OR polygon_wallet = %s;
        """, (payload.email, payload.polygon_wallet))
        existing_pub = cursor.fetchone()

        if existing_pub:
            raise HTTPException(
                status_code=400,
                detail="E-mail ou carteira Polygon já cadastrados no sistema."
            )

        # Criptografar a senha e salvar no banco
        hashed_pwd = hash_password(payload.password)
        cursor.execute("""
            INSERT INTO publishers (email, password_hash, polygon_wallet, pending_balance_usd, paid_balance_usd, status)
            VALUES (%s, %s, %s, 0.0, 0.0, 'ACTIVE')
            RETURNING id, email, polygon_wallet, created_at;
        """, (payload.email, hashed_pwd, payload.polygon_wallet))

        new_publisher = cursor.fetchone()
        conn.commit()

        # Gerar o token de login para o usuário recém-criado
        access_token = create_access_token({"sub": str(new_publisher["id"]), "email": new_publisher["email"]})

        return {
            "status": "success",
            "message": "Publisher cadastrado com sucesso",
            "publisher": {
                "id": new_publisher["id"],
                "email": new_publisher["email"],
                "polygon_wallet": new_publisher["polygon_wallet"]
            },
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/login")
async def login_publisher(payload: PublisherLoginRequest):
    """
    Autentica o publisher pelo e-mail e senha, devolvendo o Token JWT.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, email, password_hash, polygon_wallet, status
            FROM publishers 
            WHERE email = %s;
        """, (payload.email,))
        publisher = cursor.fetchone()

        if not publisher or not verify_password(payload.password, publisher["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos."
            )

        if publisher["status"] != "ACTIVE":
            raise HTTPException(status_code=403, detail="Conta inativa ou suspensa.")

        access_token = create_access_token({"sub": str(publisher["id"]), "email": publisher["email"]})

        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "publisher": {
                "id": publisher["id"],
                "email": publisher["email"],
                "polygon_wallet": publisher["polygon_wallet"]
            }
        }

    finally:
        cursor.close()
        conn.close()