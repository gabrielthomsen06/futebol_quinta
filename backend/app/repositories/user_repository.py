"""Acesso a dados do administrador."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.scalars(stmt).first()


def get_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def add(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user
