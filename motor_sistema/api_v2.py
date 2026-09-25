from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.activos.universos import (
    listar_universos,
    obtener_universo,
)
from core.datos.cache_datos import CACHE_DATOS
from core.modelos.registro_modelos import (
    listar_modelos,
)
from motor_sistema.comprobar_sistema_v2 import (
    comprobar_sistema,
)
from motor_sistema.orquestador_universal import (
    analizar_activo_completo,
)
from motor_sistema.orquestador_universo import (
    analizar_universo_completo,
)
from motor_sistema.workspaces import (
    cargar_watchlists,
    obtener_watchlist,
)


def serializar_json(
    valor: Any,
) -> Any:
    """Convierte estructuras internas a JSON seguro."""

    if valor is None:
        return None

    if isinstance(
        valor,
        (
            str,
            bool,
            int,
        ),
    ):
        return valor

    if isinstance(
        valor,
        float,
    ):
        if not math.isfinite(
            valor
        ):
            return None

        return valor

    if isinstance(
        valor,
        np.generic,
    ):
        return serializar_json(
            valor.item()
        )

    if isinstance(
        valor,
        np.ndarray,
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor.tolist()
        ]

    if isinstance(
        valor,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):
        return valor.isoformat()

    if isinstance(
        valor,
        Path,
    ):
        return str(
            valor
        )

    if isinstance(
        valor,
        pd.DataFrame,
    ):
        return [
            serializar_json(
                fila
            )
            for fila in valor.to_dict(
                orient="records"
            )
        ]

    if isinstance(
        valor,
        pd.Series,
    ):
        return {
            str(clave): serializar_json(
                dato
            )
            for clave, dato
            in valor.to_dict().items()
        }

    if isinstance(
        valor,
        pd.Index,
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor.tolist()
        ]

    if is_dataclass(
        valor
    ):
        return serializar_json(
            asdict(
                valor
            )
        )

    if isinstance(
        valor,
        dict,
    ):
        return {
            str(clave): serializar_json(
                dato
            )
            for clave, dato
            in valor.items()
        }

    if isinstance(
        valor,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor
        ]

    if pd.isna(
        valor
    ):
        return None

    return str(
        valor
    )


def api_health() -> dict[str, object]:
    """Devuelve el estado general del sistema."""

    correcto, checks = comprobar_sistema(
        comprobar_datos=False
    )

    resultado = {
        "operativo": correcto,
        "checks": checks,
        "cache": CACHE_DATOS.estadisticas(),
        "modelos": listar_modelos(),
        "universos": listar_universos(),
    }

    return serializar_json(
        resultado
    )


def api_activo(
    simbolo: str,
    horizonte: int = 20,
) -> dict[str, object]:
    """Ejecuta análisis completo de un activo."""

    resultado = analizar_activo_completo(
        simbolo=simbolo,
        horizonte_forecast=horizonte,
    )

    return serializar_json(
        resultado
    )


def _serializar_resultado_universo(
    nombre: str,
    simbolos: list[str],
    resultado,
) -> dict[str, object]:
    """Normaliza la respuesta de un universo."""

    pesos = (
        resultado.portfolio.pesos
        .reset_index()
    )

    primera_columna = (
        pesos.columns[
            0
        ]
    )

    pesos = pesos.rename(
        columns={
            primera_columna: "simbolo",
        }
    )

    respuesta = {
        "nombre": nombre.upper(),
        "simbolos": simbolos,
        "ranking": resultado.ranking,
        "pesos": pesos,
        "riesgo": resultado.riesgo,
        "factor_anual": (
            resultado.portfolio.factor_anual
        ),
    }

    return serializar_json(
        respuesta
    )


def api_universo(
    nombre: str,
) -> dict[str, object]:
    """Analiza un universo completo."""

    simbolos = obtener_universo(
        nombre
    )

    resultado = analizar_universo_completo(
        simbolos
    )

    return _serializar_resultado_universo(
        nombre=nombre,
        simbolos=simbolos,
        resultado=resultado,
    )


def api_watchlists() -> dict[str, list[str]]:
    """Devuelve las watchlists configuradas."""

    return serializar_json(
        cargar_watchlists()
    )


def api_watchlist(
    nombre: str,
) -> dict[str, object]:
    """Analiza una watchlist como universo."""

    simbolos = obtener_watchlist(
        nombre
    )

    resultado = analizar_universo_completo(
        simbolos
    )

    return _serializar_resultado_universo(
        nombre=nombre,
        simbolos=simbolos,
        resultado=resultado,
    )