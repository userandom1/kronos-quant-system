from __future__ import annotations

import json
import re
import logging
from threading import RLock
from pathlib import Path

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


from core.serializacion import serializar_json
from motor_opciones.movimiento_esperado import calcular_movimiento_esperado


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

    resultado = ejecutar_serializado(analizar_activo_completo,
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

    resultado = ejecutar_serializado(analizar_universo_completo,
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

    resultado = ejecutar_serializado(analizar_universo_completo,
        simbolos
    )

    return _serializar_resultado_universo(
        nombre=nombre,
        simbolos=simbolos,
        resultado=resultado,
    )

_LOCK_ANALISIS = RLock()


def ejecutar_serializado(funcion, *args, **kwargs):
    """Protege el predictor compartido; Starlette ejecuta las rutas en hilos."""
    with _LOCK_ANALISIS:
        return funcion(*args, **kwargs)


def api_informe(simbolo: str) -> dict[str, object]:
    """Lee el informe persistido más reciente, validando el segmento de ruta."""
    from core.activos import resolver_activo
    simbolo = resolver_activo(simbolo).simbolo
    if not re.fullmatch(r"[A-Z0-9^=_.-]{1,40}", simbolo):
        raise ValueError("Símbolo no válido.")
    nombre = re.sub(r"[^A-Za-z0-9_.-]", "_", simbolo).strip("._")
    if not nombre:
        raise ValueError("Símbolo vacío.")
    base = Path(__file__).resolve().parents[1] / "resultados" / "deep_research"
    candidatos = sorted((base / nombre).glob("*/informe.json"), reverse=True)
    if not candidatos:
        raise FileNotFoundError(simbolo)
    archivo = candidatos[0]
    informe = json.loads(archivo.read_text(encoding="utf-8"))
    # Compatibilidad: recalcular en memoria sin alterar el informe histórico.
    if "expected_move_por_vencimiento" not in informe:
        import pandas as pd
        cadena = archivo.parent / "cadena_opciones.csv"
        if cadena.exists():
            try:
                descartados = archivo.parent / "contratos_rechazados.csv"
                rechazos = pd.read_csv(descartados) if descartados.exists() else None
                tabla = calcular_movimiento_esperado(
                    pd.read_csv(cadena), float(informe["resumen"]["spot"]), rechazados=rechazos,
                )
                informe["expected_move_por_vencimiento"] = serializar_json(tabla)
                informe["procedencia_expected_move"] = {
                    "modo": "RECALCULADO_HISTORICO_EN_MEMORIA", "cadena": str(cadena),
                    "fecha_snapshot": archivo.parent.name,
                }
            except (ValueError, KeyError, OSError) as error:
                logging.getLogger(__name__).warning("Expected Move histórico %s: %s", simbolo, error)
                informe["error_expected_move"] = str(error)
    return informe
