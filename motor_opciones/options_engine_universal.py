from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.activos import Activo
from core.datos import obtener_proveedor
from motor_opciones.cadena_opciones import (
    enriquecer_cadena,
    obtener_cadena,
    obtener_vencimientos,
)
from motor_opciones.metricas_cadena import (
    resumir_cadena,
)


@dataclass(slots=True)
class ResultadoOptionsEngine:
    """Resultado del Options Engine Universal."""

    activo: Activo
    spot: float
    vencimiento: str
    cadena: pd.DataFrame
    resumen: dict[str, float | int]


def seleccionar_vencimiento(
    vencimientos: list[str],
    solicitado: str | None = None,
) -> str:
    """Selecciona vencimiento solicitado o el más cercano."""

    if not vencimientos:
        raise RuntimeError(
            "No hay vencimientos disponibles."
        )

    if solicitado is not None:
        if solicitado not in vencimientos:
            raise ValueError(
                f"Vencimiento no disponible: "
                f"{solicitado}"
            )

        return solicitado

    return vencimientos[0]


def ejecutar_options_engine(
    activo: Activo,
    vencimiento: str | None = None,
) -> ResultadoOptionsEngine:
    """Ejecuta el análisis universal de opciones."""

    if not activo.capacidades.opciones:
        raise RuntimeError(
            f"{activo.simbolo} no tiene "
            "capacidad de opciones habilitada."
        )

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    spot = proveedor.obtener_precio_actual(
        activo
    )

    vencimientos = obtener_vencimientos(
        activo
    )

    vencimiento_final = seleccionar_vencimiento(
        vencimientos,
        vencimiento,
    )

    cadena = obtener_cadena(
        activo,
        vencimiento_final,
    )

    cadena = enriquecer_cadena(
        cadena,
        spot,
    )

    resumen = resumir_cadena(
        cadena
    )

    return ResultadoOptionsEngine(
        activo=activo,
        spot=spot,
        vencimiento=vencimiento_final,
        cadena=cadena,
        resumen=resumen,
    )