"""Configuração de log.

Antes desta fase não havia nenhuma: os módulos criavam loggers e herdavam o
que o uvicorn tivesse configurado, sem nível controlável nem formato próprio.
Quando algo dá errado em produção, o log é a única testemunha.
"""

from logging.config import dictConfig

from app.core.config import settings

FORMATO = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"


def configurar_logs() -> None:
    dictConfig(
        {
            "version": 1,
            # Não desativa os loggers do uvicorn, que já estão de pé.
            "disable_existing_loggers": False,
            "formatters": {
                "padrao": {"format": FORMATO, "datefmt": "%Y-%m-%d %H:%M:%S"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "padrao",
                    # stdout: é onde o driver de log do Docker recolhe.
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {"handlers": ["console"], "level": settings.log_level.upper()},
            "loggers": {
                # O log de acesso é ruído em produção: o proxy já registra
                # cada requisição, e duplicar só enche o disco mais rápido.
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": "WARNING" if settings.is_production else "INFO",
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": settings.log_level.upper(),
                    "propagate": False,
                },
            },
        }
    )
