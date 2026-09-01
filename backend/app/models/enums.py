"""Domínios fechados do modelo, compartilhados por models, schemas e services."""

from enum import Enum


class PlayerStatus(str, Enum):
    """Inativar preserva todo o histórico — jogador nunca é excluído."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MatchStatus(str, Enum):
    """Somente PLAYED entra nas estatísticas."""

    SCHEDULED = "SCHEDULED"
    PLAYED = "PLAYED"
    CANCELLED = "CANCELLED"


class RankingMetric(str, Enum):
    """Métricas de ranking.

    Não é um domínio do banco: é o vocabulário que traduz o `?metric=` da URL
    para uma expressão de ordenação num dicionário fechado. Nenhum valor fora
    desta lista chega ao SQL.
    """

    GOALS = "goals"
    ASSISTS = "assists"
    WINS = "wins"
    GAMES = "games"
    GOALS_PER_GAME = "goals_per_game"
    ASSISTS_PER_GAME = "assists_per_game"


# Rankings de média só fazem sentido com um piso de partidas: sem ele, quem
# jogou uma vez e fez 3 gols lidera com 3,00 e nunca mais é alcançado.
AVERAGE_METRICS = frozenset({RankingMetric.GOALS_PER_GAME, RankingMetric.ASSISTS_PER_GAME})
MIN_GAMES_FOR_AVERAGE = 3

# Comprimento das colunas VARCHAR correspondentes.
PLAYER_STATUS_LENGTH = 8
MATCH_STATUS_LENGTH = 12
