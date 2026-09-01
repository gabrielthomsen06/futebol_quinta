"""Models do domínio.

Importados aqui para que o Alembic enxergue todas as tabelas no metadata.
"""

from app.models.enums import MatchStatus, PlayerStatus
from app.models.match import Match
from app.models.participation import MatchParticipation
from app.models.player import Player
from app.models.user import User

__all__ = [
    "Match",
    "MatchParticipation",
    "MatchStatus",
    "Player",
    "PlayerStatus",
    "User",
]
