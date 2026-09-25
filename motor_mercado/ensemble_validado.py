from __future__ import annotations

import pandas as pd

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from core.modelos.registro_modelos import (
    obtener_modelo,
)
from motor_mercado.seleccion_modelos import (
    calcular_pesos_modelos,
)


def ejecutar_ensemble_validado(
    simbolo: str,
    benchmark: pd.DataFrame,
    horizonte: int,
) -> dict[str, object]:
    """Genera forecast ponderado por validación."""

    activo = resolver_activo(
        simbolo
    )

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    datos = proveedor.obtener_historico(
        activo=activo,
        periodo="5y",
        intervalo="1d",
    )

    pesos = calcular_pesos_modelos(
        benchmark
    )

    predicciones = []

    retorno_ensemble = 0.0

    for nombre, peso in pesos.items():
        modelo = obtener_modelo(
            nombre
        )

        prediccion = modelo.predecir(
            activo=activo,
            datos=datos,
            horizonte=horizonte,
        )

        retorno_ensemble += (
            prediccion.retorno_estimado
            * peso
        )

        predicciones.append(
            {
                "modelo": nombre,
                "peso": peso,
                "retorno": (
                    prediccion.retorno_estimado
                ),
                "precio": (
                    prediccion.precio_estimado
                ),
            }
        )

    precio_actual = float(
        datos[
            "close"
        ].iloc[-1]
    )

    precio_estimado = (
        precio_actual
        * (
            1.0
            + retorno_ensemble
        )
    )

    return {
        "simbolo": simbolo,
        "horizonte": horizonte,
        "precio_actual": precio_actual,
        "precio_estimado": (
            precio_estimado
        ),
        "retorno_estimado": (
            retorno_ensemble
        ),
        "pesos": pesos,
        "predicciones": predicciones,
    }