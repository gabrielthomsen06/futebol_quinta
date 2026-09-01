"""Autenticação — os 18 casos da Fase 4."""

from __future__ import annotations

import datetime as dt
import uuid

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import cli
from app.core import security
from app.core.config import settings
from app.models.user import User
from tests.conftest import SENHA_DO_ADMIN

LOGIN = "/api/auth/login"
ME = "/api/auth/me"


def _forjar_token(
    *,
    sub: str | None = "irrelevante",
    segredo: str | None = None,
    validade: dt.timedelta = dt.timedelta(hours=1),
) -> str:
    """Monta um token à mão para exercitar os caminhos de rejeição."""
    agora = dt.datetime.now(dt.UTC)
    payload: dict[str, object] = {
        "iat": int(agora.timestamp()),
        "exp": int((agora + validade).timestamp()),
    }
    if sub is not None:
        payload["sub"] = sub
    return jwt.encode(payload, segredo or settings.secret_key, algorithm="HS256")


def _entrar(api: TestClient, senha: str = SENHA_DO_ADMIN) -> str:
    resposta = api.post(LOGIN, json={"username": "admin", "password": senha})
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


# --------------------------------------------------------------------------
# 1–3 · login
# --------------------------------------------------------------------------


def test_login_valido(api: TestClient, admin: User) -> None:
    """1 — devolve token utilizável, com validade e tipo."""
    resposta = api.post(LOGIN, json={"username": "admin", "password": SENHA_DO_ADMIN})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["expires_at"]

    conteudo = jwt.decode(corpo["access_token"], settings.secret_key, algorithms=["HS256"])
    assert conteudo["sub"] == str(admin.id)
    # O token carrega só identidade e tempo — nada de username, papel ou senha.
    assert set(conteudo) == {"sub", "iat", "exp"}


def test_login_senha_invalida(api: TestClient, admin: User) -> None:
    """2 — 401 com mensagem genérica."""
    resposta = api.post(LOGIN, json={"username": "admin", "password": "senha-errada-1234"})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Usuário ou senha inválidos."}


def test_login_usuario_inexistente_responde_identico(api: TestClient, admin: User) -> None:
    """3 — usuário que não existe e senha errada são indistinguíveis.

    Se as respostas diferissem, o login viraria um verificador de quais
    usuários existem.
    """
    senha_errada = api.post(LOGIN, json={"username": "admin", "password": "senha-errada-1234"})
    inexistente = api.post(LOGIN, json={"username": "ninguem", "password": "senha-errada-1234"})

    assert inexistente.status_code == senha_errada.status_code == 401
    assert inexistente.json() == senha_errada.json()


# --------------------------------------------------------------------------
# 4–8, 11–13 · token e rota protegida
# --------------------------------------------------------------------------


def test_me_com_token_valido(api: TestClient, admin: User) -> None:
    """4 — identifica o autenticado e não vaza o hash."""
    token = _entrar(api)

    resposta = api.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["username"] == "admin"
    assert corpo["id"] == str(admin.id)
    assert set(corpo) == {"id", "username"}
    assert "password_hash" not in resposta.text


def test_me_com_token_invalido(api: TestClient, admin: User) -> None:
    """5 — lixo e token assinado com outra chave."""
    lixo = api.get(ME, headers={"Authorization": "Bearer isto-nao-e-um-token"})
    assert lixo.status_code == 401

    outra_chave = _forjar_token(sub=str(admin.id), segredo="outra-chave-completamente-diferente")
    forjado = api.get(ME, headers={"Authorization": f"Bearer {outra_chave}"})
    assert forjado.status_code == 401
    assert forjado.json() == {"detail": "Credenciais inválidas."}


def test_me_com_token_expirado(api: TestClient, admin: User) -> None:
    """6 — mensagem própria, para o frontend saber que é hora de relogar."""
    vencido = _forjar_token(sub=str(admin.id), validade=dt.timedelta(hours=-1))

    resposta = api.get(ME, headers={"Authorization": f"Bearer {vencido}"})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Sua sessão expirou. Entre novamente."}


def test_endpoint_protegido_sem_token(api: TestClient, admin: User) -> None:
    """7 — 401 e o header que anuncia o esquema esperado."""
    resposta = api.get(ME)

    assert resposta.status_code == 401
    assert resposta.headers["WWW-Authenticate"] == "Bearer"
    assert resposta.json() == {"detail": "Autenticação necessária."}


def test_endpoint_protegido_com_token_valido(api: TestClient, admin: User) -> None:
    """8 — o caminho feliz da dependência AdminDep."""
    token = _entrar(api)

    assert api.get(ME, headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_token_sem_sub(api: TestClient, admin: User) -> None:
    """11 — token bem assinado, mas sem identidade, não vira sessão."""
    sem_identidade = _forjar_token(sub=None)

    resposta = api.get(ME, headers={"Authorization": f"Bearer {sem_identidade}"})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Credenciais inválidas."}


def test_token_de_usuario_inexistente(api: TestClient, admin: User) -> None:
    """12 — prova que a dependência carrega o usuário do banco.

    O token está perfeito: assinatura correta, dentro da validade. Mas aponta
    para alguém que não existe, e isso basta para recusar.
    """
    fantasma = _forjar_token(sub=str(uuid.uuid4()))

    resposta = api.get(ME, headers={"Authorization": f"Bearer {fantasma}"})

    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "cabecalho",
    ["Basic Zm9vOmJhcg==", "Bearer", "Bearer ", "token-solto-sem-esquema", ""],
)
def test_header_authorization_malformado(
    api: TestClient, admin: User, cabecalho: str
) -> None:
    """13 — todo formato estranho vira 401, nunca 500."""
    resposta = api.get(ME, headers={"Authorization": cabecalho})

    assert resposta.status_code == 401
    assert "detail" in resposta.json()


# --------------------------------------------------------------------------
# 9–10, 14 · segredos e rotas públicas
# --------------------------------------------------------------------------


def test_secret_nao_exposto(api: TestClient, admin: User) -> None:
    """9 — nem o segredo nem o hash saem pela API.

    O hash é verificado olhando os campos declarados em cada schema, e não
    procurando a palavra no texto: a descrição de um schema pode mencionar
    "password_hash" justamente para explicar que ele não está lá.
    """
    token = _entrar(api)

    openapi = api.get("/openapi.json")
    me = api.get(ME, headers={"Authorization": f"Bearer {token}"})

    # O segredo não pode aparecer em lugar nenhum, nem literalmente.
    for resposta in (openapi, me):
        assert settings.secret_key not in resposta.text

    # Nenhum schema de resposta declara o hash como campo.
    schemas = openapi.json()["components"]["schemas"]
    for nome, schema in schemas.items():
        assert "password_hash" not in schema.get("properties", {}), nome

    assert "password_hash" not in me.json()


def test_senha_nunca_armazenada_em_texto_puro(session: Session, admin: User) -> None:
    """10 — no banco existe hash bcrypt, e só."""
    guardado = admin.password_hash

    assert guardado != SENHA_DO_ADMIN
    assert SENHA_DO_ADMIN not in guardado
    assert guardado.startswith("$2b$")
    assert len(guardado) == 60
    assert bcrypt.checkpw(SENHA_DO_ADMIN.encode(), guardado.encode())


@pytest.mark.parametrize(
    "rota",
    ["/api/health", "/api/players", "/api/matches", "/api/rankings"],
)
def test_rotas_publicas_continuam_publicas(api: TestClient, rota: str) -> None:
    """14 — a garantia de não ter fechado o site sem querer."""
    assert api.get(rota).status_code == 200


# --------------------------------------------------------------------------
# 15–17 · create-admin
# --------------------------------------------------------------------------


def test_create_admin_cria_a_partir_do_ambiente(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """15 — a senha vem do ambiente e vira hash."""
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-vinda-do-ambiente")

    senha = cli._obter_senha()
    acao = cli.create_admin(session, "admin", senha)

    assert acao == "criado"
    criado = session.query(User).filter_by(username="admin").one()
    assert criado.password_hash.startswith("$2b$")
    assert security.verify_password("senha-vinda-do-ambiente", criado.password_hash)


def test_create_admin_e_idempotente(session: Session) -> None:
    """16 — a segunda execução troca a senha, não duplica o usuário."""
    assert cli.create_admin(session, "admin", "primeira-senha-1234") == "criado"
    hash_inicial = session.query(User).filter_by(username="admin").one().password_hash

    assert cli.create_admin(session, "admin", "segunda-senha-98765") == "atualizado"

    usuarios = session.query(User).filter_by(username="admin").all()
    assert len(usuarios) == 1
    assert usuarios[0].password_hash != hash_inicial
    assert security.verify_password("segunda-senha-98765", usuarios[0].password_hash)


@pytest.mark.parametrize(
    ("senha", "motivo"),
    [
        ("curta123", "menos de 12 caracteres"),
        ("troque-esta-senha", "placeholder do .env.example"),
        ("a" * 73, "73 bytes, acima do limite do bcrypt"),
        ("ç" * 40, "40 caracteres, mas 80 bytes em UTF-8"),
    ],
)
def test_create_admin_recusa_senha_fraca(
    session: Session, senha: str, motivo: str
) -> None:
    """17 — inclui o caso em que o problema só aparece contando bytes."""
    with pytest.raises(security.PasswordPolicyError):
        cli.create_admin(session, "admin", senha)

    assert session.query(User).filter_by(username="admin").first() is None, motivo


# --------------------------------------------------------------------------
# 18 · limite do bcrypt no login
# --------------------------------------------------------------------------


def test_login_com_senha_muito_longa(api: TestClient, admin: User) -> None:
    """18 — o limite de 72 bytes do bcrypt 5 não pode derrubar o endpoint.

    Senha longa demais é senha errada: 401, nunca 500.
    """
    resposta = api.post(LOGIN, json={"username": "admin", "password": "x" * 500})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Usuário ou senha inválidos."}
