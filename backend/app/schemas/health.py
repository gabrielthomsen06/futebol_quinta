from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = Field(description="Situação geral da API")
    database: Literal["ok", "erro"] = Field(description="Resultado de um SELECT 1 no Postgres")
    app: str
    version: str
    season: int
