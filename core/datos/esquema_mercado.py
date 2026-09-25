from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


COLUMNAS_OHLCV = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]


COLUMNAS_OPCIONES = [
    "subyacente",
    "vencimiento",
    "strike",
    "tipo_opcion",
    "bid",
    "ask",
    "ultimo",
    "volumen",
    "open_interest",
    "iv",
    "in_the_money",
    "contract_symbol",
    "fuente",
]


@dataclass(frozen=True, slots=True)
class MetadatosMercado:
    """Metadatos asociados a una serie de mercado."""

    simbolo: str
    clase_activo: str
    divisa: str
    proveedor: str
    intervalo: str


def validar_ohlcv(
    datos: pd.DataFrame,
) -> None:
    """
    Valida que un DataFrame respete el esquema OHLCV universal.

    Lanza ValueError si el formato no es válido.
    """

    if datos.empty:
        raise ValueError(
            "El DataFrame OHLCV está vacío."
        )

    if not isinstance(
        datos.index,
        pd.DatetimeIndex,
    ):
        raise ValueError(
            "El índice OHLCV debe ser DatetimeIndex."
        )

    faltantes = [
        columna
        for columna in COLUMNAS_OHLCV
        if columna not in datos.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas OHLCV obligatorias: "
            f"{faltantes}"
        )

    if not datos.index.is_monotonic_increasing:
        raise ValueError(
            "El índice temporal debe estar ordenado."
        )

    if datos.index.has_duplicates:
        raise ValueError(
            "El índice temporal contiene duplicados."
        )


def validar_opciones(
    datos: pd.DataFrame,
) -> None:
    """Valida el esquema universal de opciones."""

    if datos.empty:
        raise ValueError(
            "La cadena de opciones está vacía."
        )

    faltantes = [
        columna
        for columna in COLUMNAS_OPCIONES
        if columna not in datos.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas de opciones obligatorias: "
            f"{faltantes}"
        )


def asignar_metadatos(
    datos: pd.DataFrame,
    metadatos: MetadatosMercado,
) -> pd.DataFrame:
    """Añade metadatos estándar mediante DataFrame.attrs."""

    resultado = datos.copy()

    resultado.attrs[
        "simbolo"
    ] = metadatos.simbolo

    resultado.attrs[
        "clase_activo"
    ] = metadatos.clase_activo

    resultado.attrs[
        "divisa"
    ] = metadatos.divisa

    resultado.attrs[
        "proveedor"
    ] = metadatos.proveedor

    resultado.attrs[
        "intervalo"
    ] = metadatos.intervalo

    return resultado