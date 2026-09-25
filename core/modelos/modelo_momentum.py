from __future__ import annotations

import numpy as np
import pandas as pd

from core.activos.modelo_activo import Activo
from core.modelos.modelo_base import (
    ModeloForecast,
    ResultadoForecast,
)


class ModeloMomentum(ModeloForecast):
    """Modelo baseline de continuación de momentum."""

    nombre = "MOMENTUM"

    def __init__(
        self,
        ventana: int = 20,
    ) -> None:
        self.ventana = ventana

    def predecir(
        self,
        activo: Activo,
        datos: pd.DataFrame,
        horizonte: int,
    ) -> ResultadoForecast:
        """Proyecta momentum reciente al horizonte solicitado."""

        cierre = datos[
            "close"
        ].dropna()

        if len(cierre) <= self.ventana:
            raise RuntimeError(
                f"Histórico insuficiente para "
                f"{activo.simbolo}."
            )

        precio_actual = float(
            cierre.iloc[-1]
        )

        precio_pasado = float(
            cierre.iloc[
                -1 - self.ventana
            ]
        )

        retorno_ventana = (
            precio_actual
            / precio_pasado
            - 1.0
        )

        retorno_diario_equivalente = (
            (
                1.0
                + retorno_ventana
            )
            ** (
                1.0
                / self.ventana
            )
            - 1.0
        )

        retorno_estimado = float(
            (
                1.0
                + retorno_diario_equivalente
            )
            ** horizonte
            - 1.0
        )

        precio_estimado = (
            precio_actual
            * (
                1.0
                + retorno_estimado
            )
        )

        retornos = (
            cierre
            .pct_change()
            .dropna()
            .tail(
                self.ventana
            )
        )

        dispersion = float(
            retornos.std(
                ddof=1
            )
            * np.sqrt(
                horizonte
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
                "retorno_ventana": (
                    retorno_ventana
                ),
                "dispersion_horizonte": (
                    dispersion
                ),
            },
        )