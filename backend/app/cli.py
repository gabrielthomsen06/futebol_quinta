"""Comandos administrativos de linha de comando.

    python -m app.cli create-admin

O comando `seed` (dados fictícios de desenvolvimento) entra na Fase 7.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal, transaction
from app.models.user import User
from app.repositories import user_repository


def create_admin(session: Session, username: str, password: str) -> str:
    """Cria ou atualiza o administrador único. Devolve 'criado' ou 'atualizado'.

    Idempotente de propósito: rodar de novo troca a senha em vez de duplicar
    usuário. É assim que a troca de senha acontece no MVP — não existe tela
    para isso, e nem precisa existir.
    """
    username = username.strip()
    if not username:
        raise security.PasswordPolicyError("O nome de usuário não pode ser vazio.")

    security.validate_password_policy(password)

    with transaction(session):
        admin = user_repository.get_by_username(session, username)
        if admin is None:
            user_repository.add(
                session,
                User(
                    username=username,
                    password_hash=security.hash_password(password),
                ),
            )
            acao = "criado"
        else:
            admin.password_hash = security.hash_password(password)
            acao = "atualizado"

    return acao


def _obter_senha() -> str:
    """Lê a senha do ambiente ou pergunta no terminal.

    Nunca aceita a senha como argumento de linha de comando: ela ficaria no
    histórico do shell e na listagem de processos.
    """
    senha = os.environ.get("ADMIN_PASSWORD", "")
    if senha:
        return senha

    senha = getpass.getpass("Senha do administrador: ")
    confirmacao = getpass.getpass("Repita a senha: ")
    if senha != confirmacao:
        raise security.PasswordPolicyError("As senhas não conferem.")
    return senha


def _comando_create_admin() -> int:
    try:
        senha = _obter_senha()
        session = SessionLocal()
        try:
            acao = create_admin(session, settings.admin_username, senha)
        finally:
            session.close()
    except security.PasswordPolicyError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    print(f"Administrador '{settings.admin_username}' {acao}.")
    print(
        "A senha não é exibida. Se ADMIN_PASSWORD estiver no .env, você já pode "
        "removê-la: o hash está no banco e nada mais lê essa variável."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Comandos administrativos do SÓ NO MIGUÉ FC.",
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    subcomandos.add_parser(
        "create-admin",
        help="Cria ou atualiza o administrador único a partir do ambiente.",
    )

    args = parser.parse_args(argv)
    if args.comando == "create-admin":
        return _comando_create_admin()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
