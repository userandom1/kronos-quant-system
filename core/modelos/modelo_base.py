from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from core.activos.modelo_activo import Activo


@dataclass(frozen=True, slots=True)
class ResultadoForecast:
    """Resultado normalizado de cualquier modelo predictivo."""

    simbolo: str
    modelo: str
    horizonte: int

    precio_actual: float
    precio_estimado: float
    retorno_estimado: float

    confianza: float | None = None
    metadata: dict[str, object] | None = None


class ModeloForecast(ABC):
    """Interfaz común para modelos predictivos."""

    nombre: str

    @abstractmethod
    def predecir(
        self,
        activo: Activo,
        datos: pd.DataFrame,
        horizonte: int,
    ) -> ResultadoForecast:
        """Genera una predicción para un activo."""