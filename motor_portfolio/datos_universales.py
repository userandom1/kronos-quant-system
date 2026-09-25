from __future__ import annotations

import pandas as pd

from core.activos import resolver_activo
from core.activos.clases_activo import ClaseActivo
from core.datos import obtener_proveedor


def descargar_precios_universo(
    simbolos: list[str],
    periodo: str = "5y",
) -> pd.DataFrame:
    """Descarga cierres normalizados para múltiples activos."""

    series: list[pd.Series] = []

    for simbolo in simbolos:
        activo = resolver_activo(
            simbolo
        )

        proveedor = obtener_proveedor(
            activo.proveedor
        )

        datos = proveedor.obtener_historico(
            activo=activo,
            periodo=periodo,
            intervalo="1d",
        )

        cierre = datos[
            "close"
        ].rename(
            activo.simbolo
        )

        series.append(
            cierre
        )

    precios = pd.concat(
        series,
        axis=1,
        join="inner",
    )

    precios = (
        precios
        .sort_index()
        .dropna()
    )

    if len(precios) < 100:
        raise RuntimeError(
            "Histórico común insuficiente."
        )

    return precios


def calcular_retornos(
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula retornos simples diarios."""

    return (
        precios
        .pct_change()
        .dropna()
    )


def sesiones_anuales(
    simbolos: list[str],
) -> int:
    """Determina el factor anual aproximado."""

    activos = [
        resolver_activo(
            simbolo
        )
        for simbolo in simbolos
    ]

    if all(
        activo.clase == ClaseActivo.CRYPTO
        for activo in activos
    ):
        return 365

    return 252