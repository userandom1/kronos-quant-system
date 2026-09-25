from __future__ import annotations

import numpy as np
import pandas as pd

from core.activos.modelo_activo import Activo
from core.modelos.modelo_base import (
    ModeloForecast,
    ResultadoForecast,
)


class ModeloDrift(ModeloForecast):
    """Baseline basado en drift histórico logarítmico."""

    nombre = "DRIFT"

    def __init__(
        self,
        ventana: int = 60,
    ) -> None:
        self.ventana = ventana

    def predecir(
        self,
        activo: Activo,
        datos: pd.DataFrame,
        horizonte: int,
    ) -> ResultadoForecast:
        """Proyecta el drift medio reciente."""

        cierre = datos[
            "close"
        ].dropna()

        if len(cierre) < (
            self.ventana + 1
        ):
            raise RuntimeError(
                f"Histórico insuficiente para "
                f"{activo.simbolo}."
            )

        retornos = np.log(
            cierre
            / cierre.shift(1)
        ).dropna().tail(
            self.ventana
        )

        drift_diario = float(
            retornos.mean()
        )

        precio_actual = float(
            cierre.iloc[-1]
        )

        retorno_estimado = float(
            np.exp(
                drift_diario
                * horizonte
            )
            - 1.0
        )

        precio_estimado = (
            precio_actual
            * (
                1.0
                + retorno_estimado
            )
        )

        volatilidad = float(
            retornos.std(
                ddof=1
            )
        )

        return ResultadoForecast(
            simbolo=activo.simbolo,
            modelo=self.nombre,
            horizonte=horizonte,
            precio_actual=precio_actual,
            precio_estimado=precio_estimado,
            retorno_estimado=retorno_estimado,
            metadata={
                "ventana": self.ventana,
                "drift_diario": drift_diario,
                "volatilidad_diaria": volatilidad,
            },
        )