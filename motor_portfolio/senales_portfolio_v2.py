from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_SENALES = (
    RUTA_BASE
    / "resultados"
    / "senales_v2"
    / "senales_v2.csv"
)


def cargar_senales() -> pd.DataFrame:
    """Carga las señales oficiales V2."""

    if not RUTA_SENALES.exists():
        raise FileNotFoundError(
            f"No existe: {RUTA_SENALES}"
        )

    datos = pd.read_csv(
        RUTA_SENALES
    )

    return datos


def normalizar_zscore(
    serie: pd.Series,
) -> pd.Series:
    """Normaliza una serie transversalmente."""

    serie = pd.to_numeric(
        serie,
        errors="coerce",
    )

    desviacion = serie.std(
        ddof=0
    )

    if (
        not np.isfinite(desviacion)
        or desviacion == 0
    ):
        return pd.Series(
            0.0,
            index=serie.index,
        )

    return (
        serie - serie.mean()
    ) / desviacion


def construir_alpha_proxy(
    datos: pd.DataFrame,
    peso_20d: float = 0.40,
    peso_60d: float = 0.60,
) -> pd.Series:
    """Combina las señales 20D y 60D en un alpha proxy."""

    if not np.isclose(
        peso_20d + peso_60d,
        1.0,
    ):
        raise ValueError(
            "Los pesos de señales deben sumar 1."
        )

    z20 = normalizar_zscore(
        datos["signal_20d"]
    )

    z60 = normalizar_zscore(
        datos["signal_60d"]
    )

    alpha = (
        peso_20d * z20
        + peso_60d * z60
    )

    alpha.index = datos[
        "ticker"
    ]

    alpha.name = "alpha_proxy"

    return alpha