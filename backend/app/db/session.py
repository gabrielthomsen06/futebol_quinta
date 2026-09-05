"""Engine, fábrica de sessões e o limite de transação.

SQLAlchemy síncrono por decisão de arquitetura (D7): o FastAPI executa os
endpoints `def` em threadpool, o que é suficiente para a escala desta aplicação
e evita toda a classe de problemas de event loop.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    # Derruba conexões que o banco fechou por inatividade antes de usá-las.
    pool_pre_ping=True,
    # O limite do pool não é afinação de desempenho: é o que impede a
    # aplicação de estourar o teto de conexões do plano do banco. Cada worker
    # do uvicorn abre o seu próprio pool, então o total é multiplicado por
    # eles. Ver a justificativa dos valores em core/config.py.
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
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


@contextmanager
def transaction(session: Session) -> Iterator[None]:
    """Delimita a transação no service — repository nunca dá commit.

    Tudo que acontece dentro do bloco vira uma escrita só. É isso que impede
    uma partida de ficar gravada pela metade: se a inserção da escalação
    falhar no meio, a partida inteira volta atrás.
    """
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
