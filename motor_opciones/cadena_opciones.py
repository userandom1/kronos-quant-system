from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from core.activos import Activo
from core.datos import (
    DatosNoDisponiblesError,
    obtener_proveedor,
)


def obtener_vencimientos(
    activo: Activo,
) -> list[str]:
    """Obtiene los vencimientos disponibles del activo."""

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    return proveedor.listar_vencimientos_opciones(
        activo
    )


def obtener_cadena(
    activo: Activo,
    vencimiento: str,
) -> pd.DataFrame:
    """Obtiene una cadena universal de opciones."""

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    cadena = proveedor.obtener_cadena_opciones(
        activo=activo,
        vencimiento=vencimiento,
    )

    if cadena.empty:
        raise DatosNoDisponiblesError(
            f"Cadena vacía para {activo.simbolo}."
        )

    return cadena


def enriquecer_cadena(
    cadena: pd.DataFrame,
    spot: float,
) -> pd.DataFrame:
    """Añade métricas universales a la cadena."""

    resultado = cadena.copy()

    resultado["spot"] = float(
        spot
    )

    resultado["mid"] = (
        resultado["bid"]
        + resultado["ask"]
    ) / 2.0

    resultado["spread"] = (
        resultado["ask"]
        - resultado["bid"]
    )

    resultado["spread_pct"] = np.where(
        resultado["mid"] > 0,
        resultado["spread"]
        / resultado["mid"],
        np.nan,
    )

    resultado["moneyness"] = (
        resultado["strike"]
        / spot
    )

    resultado["distancia_spot_pct"] = (
        resultado["strike"]
        / spot
        - 1.0
    )

    resultado["premium_proxy"] = (
        resultado["mid"]
        * resultado["volumen"].fillna(0)
        * 100.0
    )

    vencimiento = pd.to_datetime(
        resultado["vencimiento"],
        errors="coerce",
    )

    hoy = pd.Timestamp(
        datetime.now().date()
    )

    resultado["dte"] = (
        vencimiento
        - hoy
    ).dt.days

    return resultado