from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from core.modelos.registro_modelos import (
    listar_modelos,
    obtener_modelo,
)


def ejecutar_forecast(
    simbolo: str,
    horizonte: int = 20,
    modelos: list[str] | None = None,
) -> pd.DataFrame:
    """Ejecuta varios modelos sobre un activo."""

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

    modelos_finales = (
        modelos
        if modelos is not None
        else listar_modelos()
    )

    resultados: list[
        dict[str, object]
    ] = []

    for nombre in modelos_finales:
        modelo = obtener_modelo(
            nombre
        )

        resultado = modelo.predecir(
            activo=activo,
            datos=datos,
            horizonte=horizonte,
        )

        fila = asdict(
            resultado
        )

        metadata = fila.pop(
            "metadata"
        )

        if metadata:
            for clave, valor in metadata.items():
                fila[
                    f"meta_{clave}"
                ] = valor

        resultados.append(
            fila
        )

    return pd.DataFrame(
        resultados
    )


def construir_ensemble_simple(
    resultados: pd.DataFrame,
) -> dict[str, float]:
    """Construye ensemble medio sin pesos optimizados."""

    retorno = float(
        resultados[
            "retorno_estimado"
        ].mean()
    )

    precio_actual = float(
        resultados[
            "precio_actual"
        ].iloc[0]
    )

    precio_estimado = (
        precio_actual
        * (
            1.0
            + retorno
        )
    )

    dispersion_modelos = float(
        resultados[
            "retorno_estimado"
        ].std(
            ddof=0
        )
    )

    return {
        "precio_actual": precio_actual,
        "precio_estimado": precio_estimado,
        "retorno_estimado": retorno,
        "dispersion_modelos": (
            dispersion_modelos
        ),
    }