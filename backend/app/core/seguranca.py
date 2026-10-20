"""Hash de senhas (bcrypt) e emissão/validação de tokens JWT (HS256)."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import obter_configuracoes

ALGORITMO_JWT = "HS256"


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(
        senha.encode("utf-8"), bcrypt.gensalt(rounds=obter_configuracoes().rodadas_bcrypt)
    ).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        # Hash malformado ou senha acima do limite do bcrypt
        return False


def criar_token_acesso(usuario_id: int, tipo_usuario: str) -> str:
    config = obter_configuracoes()
    agora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario_id),
        "tipo_usuario": tipo_usuario,
        "iat": agora,
        "exp": agora + timedelta(minutes=config.minutos_expiracao_jwt),
    }
    return jwt.encode(carga, config.segredo_jwt, algorithm=ALGORITMO_JWT)


def decodificar_token(token: str) -> dict:
    """Decodifica o token; lança jwt.ExpiredSignatureError ou jwt.InvalidTokenError."""
    config = obter_configuracoes()
    return jwt.decode(
        token,
        config.segredo_jwt,
        algorithms=[ALGORITMO_JWT],
        options={"require": ["sub", "exp"]},
    )
