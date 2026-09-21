from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


RUTA_BASE = Path(__file__).resolve().parents[1]


ARCHIVOS_CRITICOS = {
    "market_regime_v2": (
        RUTA_BASE
        / "resultados"
        / "regimen_mercado_v2"
        / "regimen_global.csv"
    ),
    "senales_v2": (
        RUTA_BASE
        / "resultados"
        / "senales_v2"
        / "senales_v2.csv"
    ),
    "portfolio_v2": (
        RUTA_BASE
        / "resultados"
        / "portfolio_engine"
        / "v1"
        / "v2"
        / "pesos_portfolio_v2.csv"
    ),
    "risk_engine_v1": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "metricas_riesgo.csv"
    ),
    "options_flow_v2": (
        RUTA_BASE
        / "resultados"
        / "options_flow"
        / "QQQ"
        / "v2"
        / "resumen_flow_v2.csv"
    ),
    "dealer_v4": (
        RUTA_BASE
        / "resultados"
        / "dealer_engine"
        / "QQQ"
        / "v4"
        / "resumen_dealer_v4.csv"
    ),
}


def obtener_estado_archivo(
    ruta: Path,
) -> dict[str, Any]:
    """Obtiene estado y antigüedad de un archivo."""

    if not ruta.exists():
        return {
            "existe": False,
            "ruta": str(ruta),
            "modificado": None,
            "edad_horas": None,
        }

    timestamp = ruta.stat().st_mtime

    modificado = datetime.fromtimestamp(
        timestamp
    )

    ahora = datetime.now()

    edad = (
        ahora - modificado
    ).total_seconds() / 3600.0

    return {
        "existe": True,
        "ruta": str(ruta),
        "modificado": modificado.isoformat(
            timespec="seconds"
        ),
        "edad_horas": edad,
    }


def obtener_estado_sistema() -> dict[str, Any]:
    """Construye estado general del sistema."""

    detalle = {
        nombre: obtener_estado_archivo(
            ruta
        )
        for nombre, ruta
        in ARCHIVOS_CRITICOS.items()
    }

    disponibles = sum(
        1
        for item in detalle.values()
        if item["existe"]
    )

    total = len(
        detalle
    )

    if disponibles == total:
        estado = "OPERATIVO"

    elif disponibles >= total * 0.7:
        estado = "PARCIAL"

    else:
        estado = "INCOMPLETO"

    modificaciones = [
        item["modificado"]
        for item in detalle.values()
        if item["modificado"] is not None
    ]

    ultima_actualizacion = (
        max(modificaciones)
        if modificaciones
        else None
    )

    return {
        "estado": estado,
        "datasets_disponibles": disponibles,
        "datasets_totales": total,
        "ultima_actualizacion": ultima_actualizacion,
        "detalle": detalle,
    }