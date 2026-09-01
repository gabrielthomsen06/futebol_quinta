"""Engine e fábrica de sessões.

SQLAlchemy síncrono por decisão de arquitetura (D7): o FastAPI executa os
endpoints `def` em threadpool, o que é suficiente para a escala desta aplicação
e evita toda a classe de problemas de event loop.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    # Derruba conexões que o banco fechou por inatividade antes de usá-las.
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """Uma sessão por requisição, sempre fechada ao final."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
