"""Hash de senha e emissão/validação de JWT.

Única porta do projeto para criptografia. Nenhum router, service ou repository
chama bcrypt ou PyJWT diretamente.

Escolhas (Fase 4):
  - bcrypt direto, sem passlib — passlib está sem release desde 2020 e quebra
    com bcrypt >= 4.1. A abstração dele serviria para trocar de algoritmo, algo
    que uma aplicação com um usuário não vai fazer.
  - PyJWT, sempre com a lista de algoritmos explícita no decode: é o que fecha
    por construção o ataque de confusão de algoritmo (alg: none).
"""

from __future__ import annotations

import datetime as dt
import uuid
from functools import cache

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"

MIN_PASSWORD_CHARS = 12
# Limite real do bcrypt. A partir da versão 5 ele levanta ValueError acima
# disso, em vez de truncar em silêncio como fazia antes.
BCRYPT_MAX_BYTES = 72

# Valores de exemplo que circulam em .env.example e tutoriais.
_PLACEHOLDERS = frozenset(
    {"troque-esta-senha", "changeme", "admin", "senha", "password", "123456"}
)


class PasswordPolicyError(ValueError):
    """Senha recusada pela política de criação do administrador."""


class TokenError(Exception):
    """Token malformado, mal assinado ou sem identidade utilizável."""


class TokenExpiredError(TokenError):
    """Token bem formado e bem assinado, porém vencido."""


# --------------------------------------------------------------------------
# Senha
# --------------------------------------------------------------------------


def validate_password_policy(password: str) -> None:
    """Valida a senha do administrador.

    Conta caracteres para o mínimo e **bytes UTF-8** para o teto: "sãopaulo1234"
    tem 12 caracteres e 13 bytes, e é o byte que o bcrypt enxerga.

    Sem exigência de maiúscula, número ou símbolo — regra de composição empurra
    para senhas curtas e decoradas, que são piores que uma frase longa.
    """
    if len(password) < MIN_PASSWORD_CHARS:
        raise PasswordPolicyError(
            f"A senha precisa ter ao menos {MIN_PASSWORD_CHARS} caracteres."
        )

    tamanho_em_bytes = len(password.encode("utf-8"))
    if tamanho_em_bytes > BCRYPT_MAX_BYTES:
        raise PasswordPolicyError(
            f"A senha ocupa {tamanho_em_bytes} bytes e o limite do bcrypt é "
            f"{BCRYPT_MAX_BYTES}. Acentos e emoji ocupam mais de um byte cada."
        )

    if password.strip().lower() in _PLACEHOLDERS:
        raise PasswordPolicyError(
            "Essa senha é um valor de exemplo. Escolha outra."
        )


def hash_password(password: str) -> str:
    """Gera o hash bcrypt (60 caracteres, prefixo $2b$)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Confere a senha contra o hash.

    O bcrypt 5 levanta ValueError para senha acima de 72 bytes e para hash
    malformado. Senha longa demais é senha errada, não falha do servidor:
    devolvemos False para virar 401 e nunca 500.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


@cache
def dummy_hash() -> str:
    """Hash descartável para igualar o tempo de resposta.

    Quando o usuário não existe, o login ainda executa uma verificação contra
    este hash. Sem isso, a diferença de alguns centésimos de segundo revelaria
    quais nomes de usuário existem.
    """
    return hash_password("hash-usado-apenas-para-igualar-o-tempo-de-resposta")


# --------------------------------------------------------------------------
# Token
# --------------------------------------------------------------------------


def create_access_token(user_id: uuid.UUID) -> tuple[str, dt.datetime]:
    """Emite o token e devolve também quando ele expira.

    O frontend recebe a data pronta em vez de precisar decodificar o JWT —
    decodificar token no cliente é fonte clássica de bug.
    """
    agora = dt.datetime.now(dt.UTC)
    expira_em = agora + dt.timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        # Só a identidade. Token não é banco de dados, e o conteúdo dele é
        # legível por qualquer um que o tenha em mãos.
        "sub": str(user_id),
        "iat": int(agora.timestamp()),
        "exp": int(expira_em.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, expira_em


def decode_access_token(token: str) -> uuid.UUID:
    """Valida o token e devolve o id do usuário.

    `algorithms` é passado explicitamente sempre: é o que impede um token
    forjado com outro algoritmo (ou com `none`) de ser aceito.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as erro:
        raise TokenExpiredError("Token expirado.") from erro
    except jwt.PyJWTError as erro:
        raise TokenError("Token inválido.") from erro

    sub = payload.get("sub")
    if not sub:
        raise TokenError("Token sem identidade.")

    try:
        return uuid.UUID(str(sub))
    except ValueError as erro:
        raise TokenError("Identidade do token não é um UUID.") from erro


def secret_key_is_weak() -> bool:
    """Segredo padrão ou curto demais para assinar token com segurança."""
    return (
        settings.secret_key == "inseguro-apenas-para-desenvolvimento"
        or len(settings.secret_key) < 32
    )
