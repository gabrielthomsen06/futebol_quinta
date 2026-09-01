"""Acesso a dados do administrador. Consumido pela Fase 4."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.scalars(stmt).first()


def add(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user
