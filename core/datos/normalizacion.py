from __future__ import annotations

import numpy as np
import pandas as pd

from core.activos.modelo_activo import Activo
from core.datos.esquema_mercado import (
    COLUMNAS_OHLCV,
    COLUMNAS_OPCIONES,
    MetadatosMercado,
    asignar_metadatos,
    validar_ohlcv,
    validar_opciones,
)


MAPEO_OHLCV = {
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "close",
    "volume": "volume",
}


MAPEO_OPCIONES = {
    "contractSymbol": "contract_symbol",
    "lastTradeDate": "ultima_operacion",
    "strike": "strike",
    "lastPrice": "ultimo",
    "bid": "bid",
    "ask": "ask",
    "change": "cambio",
    "percentChange": "cambio_porcentual",
    "volume": "volumen",
    "openInterest": "open_interest",
    "impliedVolatility": "iv",
    "inTheMoney": "in_the_money",
    "contractSize": "tamano_contrato",
    "currency": "divisa",
}


def normalizar_ohlcv(
    datos: pd.DataFrame,
    activo: Activo,
    proveedor: str,
    intervalo: str,
) -> pd.DataFrame:
    """
    Convierte datos OHLCV externos al esquema universal.

    El resultado final siempre utiliza:
    open, high, low, close, volume.
    """

    if datos.empty:
        raise ValueError(
            f"No existen datos OHLCV para "
            f"{activo.simbolo}."
        )

    resultado = datos.copy()

    resultado = _aplanar_columnas(
        resultado
    )

    resultado.columns = [
        str(columna).strip().lower()
        for columna in resultado.columns
    ]

    resultado = resultado.rename(
        columns=MAPEO_OHLCV
    )

    # Si existen columnas repetidas tras normalizar,
    # se conserva la primera.
    resultado = resultado.loc[
        :,
        ~resultado.columns.duplicated()
    ]

    for columna in COLUMNAS_OHLCV:
        if columna not in resultado.columns:
            if columna == "volume":
                resultado[
                    columna
                ] = np.nan

            else:
                raise ValueError(
                    f"Falta la columna obligatoria "
                    f"{columna} para {activo.simbolo}."
                )

    resultado = resultado[
        COLUMNAS_OHLCV
    ].copy()

    resultado.index = pd.to_datetime(
        resultado.index,
        errors="coerce",
    )

    resultado = resultado[
        ~resultado.index.isna()
    ]

    resultado.index.name = "timestamp"

    resultado = (
        resultado
        .sort_index()
    )

    resultado = resultado[
        ~resultado.index.duplicated(
            keep="last"
        )
    ]

    for columna in COLUMNAS_OHLCV:
        resultado[
            columna
        ] = pd.to_numeric(
            resultado[columna],
            errors="coerce",
        )

    resultado = resultado.dropna(
        subset=[
            "open",
            "high",
            "low",
            "close",
        ]
    )

    metadatos = MetadatosMercado(
        simbolo=activo.simbolo,
        clase_activo=activo.clase.value,
        divisa=activo.divisa,
        proveedor=proveedor,
        intervalo=intervalo,
    )

    resultado = asignar_metadatos(
        resultado,
        metadatos,
    )

    validar_ohlcv(
        resultado
    )

    return resultado


def normalizar_opciones(
    datos: pd.DataFrame,
    activo: Activo,
    vencimiento: str,
    tipo_opcion: str,
    proveedor: str,
) -> pd.DataFrame:
    """Convierte una tabla externa al esquema universal de opciones."""

    if datos.empty:
        return pd.DataFrame(
            columns=COLUMNAS_OPCIONES
        )

    resultado = datos.copy()

    resultado = resultado.rename(
        columns=MAPEO_OPCIONES
    )

    resultado[
        "subyacente"
    ] = activo.simbolo

    resultado[
        "vencimiento"
    ] = vencimiento

    resultado[
        "tipo_opcion"
    ] = tipo_opcion.upper()

    resultado[
        "fuente"
    ] = proveedor

    columnas_numericas = [
        "strike",
        "bid",
        "ask",
        "ultimo",
        "volumen",
        "open_interest",
        "iv",
    ]

    for columna in columnas_numericas:
        if columna not in resultado.columns:
            resultado[
                columna
            ] = np.nan

        resultado[
            columna
        ] = pd.to_numeric(
            resultado[columna],
            errors="coerce",
        )

    if "in_the_money" not in resultado.columns:
        resultado[
            "in_the_money"
        ] = False

    if "contract_symbol" not in resultado.columns:
        resultado[
            "contract_symbol"
        ] = None

    resultado = resultado[
        COLUMNAS_OPCIONES
    ].copy()

    validar_opciones(
        resultado
    )

    return resultado


def _aplanar_columnas(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Convierte columnas MultiIndex a columnas simples."""

    resultado = datos.copy()

    if not isinstance(
        resultado.columns,
        pd.MultiIndex,
    ):
        return resultado

    resultado.columns = [
        columna[0]
        if isinstance(
            columna,
            tuple,
        )
        else columna
        for columna in resultado.columns
    ]

    return resultado