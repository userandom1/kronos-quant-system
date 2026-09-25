from __future__ import annotations

import numpy as np
import pandas as pd

from core.activos.modelo_activo import Activo
from core.modelos.registro_modelos import (
    obtener_modelo,
)


def construir_origenes(
    longitud: int,
    horizonte: int,
    pasos: int,
    salto: int,
    minimo_historial: int,
) -> list[int]:
    """Construye puntos de evaluación walk-forward."""

    ultimo = (
        longitud
        - horizonte
        - 1
    )

    if ultimo < minimo_historial:
        return []

    primero = max(
        minimo_historial,
        ultimo
        - (
            pasos - 1
        )
        * salto,
    )

    origenes = list(
        range(
            primero,
            ultimo + 1,
            salto,
        )
    )

    if origenes[
        -1
    ] != ultimo:
        origenes.append(
            ultimo
        )

    return origenes[
        -pasos:
    ]


def evaluar_modelo(
    activo: Activo,
    datos: pd.DataFrame,
    modelo_nombre: str,
    horizonte: int = 20,
    pasos: int = 6,
    salto: int = 20,
    minimo_historial: int = 300,
) -> tuple[
    dict[str, float | int | str],
    pd.DataFrame,
]:
    """Evalúa un modelo mediante walk-forward."""

    modelo = obtener_modelo(
        modelo_nombre
    )

    origenes = construir_origenes(
        longitud=len(
            datos
        ),
        horizonte=horizonte,
        pasos=pasos,
        salto=salto,
        minimo_historial=minimo_historial,
    )

    registros: list[
        dict[str, object]
    ] = []

    for origen in origenes:
        historico = datos.iloc[
            :origen + 1
        ].copy()

        precio_actual = float(
            datos[
                "close"
            ].iloc[
                origen
            ]
        )

        precio_real = float(
            datos[
                "close"
            ].iloc[
                origen
                + horizonte
            ]
        )

        try:
            prediccion = modelo.predecir(
                activo=activo,
                datos=historico,
                horizonte=horizonte,
            )

        except Exception as error:
            print(
                f"{modelo_nombre} | "
                f"origen {origen} | "
                f"ERROR: {error}"
            )

            continue

        retorno_real = (
            precio_real
            / precio_actual
            - 1.0
        )

        retorno_predicho = (
            prediccion.retorno_estimado
        )

        registros.append(
            {
                "modelo": modelo_nombre,
                "origen": origen,
                "fecha": datos.index[
                    origen
                ],
                "retorno_real": (
                    retorno_real
                ),
                "retorno_predicho": (
                    retorno_predicho
                ),
                "precio_real": (
                    precio_real
                ),
                "precio_predicho": (
                    prediccion.precio_estimado
                ),
            }
        )

    detalle = pd.DataFrame(
        registros
    )

    if detalle.empty:
        raise RuntimeError(
            f"No existen evaluaciones válidas "
            f"para {modelo_nombre}."
        )

    errores = (
        detalle[
            "retorno_predicho"
        ]
        - detalle[
            "retorno_real"
        ]
    )

    rmse = float(
        np.sqrt(
            np.mean(
                errores**2
            )
        )
    )

    mae = float(
        np.mean(
            np.abs(
                errores
            )
        )
    )

    direccion = float(
        np.mean(
            np.sign(
                detalle[
                    "retorno_predicho"
                ]
            )
            == np.sign(
                detalle[
                    "retorno_real"
                ]
            )
        )
    )

    if len(
        detalle
    ) >= 3:
        ic = float(
            detalle[
                "retorno_predicho"
            ].corr(
                detalle[
                    "retorno_real"
                ]
            )
        )

    else:
        ic = np.nan

    resumen = {
        "modelo": modelo_nombre,
        "horizonte": horizonte,
        "observaciones": len(
            detalle
        ),
        "rmse_retorno": rmse,
        "mae_retorno": mae,
        "direccion_acertada": direccion,
        "ic": ic,
    }

    return resumen, detalle


def ejecutar_benchmark(
    activo: Activo,
    datos: pd.DataFrame,
    modelos: list[str],
    horizonte: int = 20,
    pasos: int = 6,
    salto: int = 20,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Evalúa múltiples modelos."""

    resumenes = []
    detalles = []

    for nombre in modelos:
        print(
            f"Evaluando {nombre}..."
        )

        try:
            resumen, detalle = evaluar_modelo(
                activo=activo,
                datos=datos,
                modelo_nombre=nombre,
                horizonte=horizonte,
                pasos=pasos,
                salto=salto,
            )

            resumenes.append(
                resumen
            )

            detalles.append(
                detalle
            )

        except Exception as error:
            print(
                f"{nombre} | ERROR: {error}"
            )

    if not resumenes:
        raise RuntimeError(
            "Ningún modelo pudo evaluarse."
        )

    resumen = pd.DataFrame(
        resumenes
    )

    detalle_total = pd.concat(
        detalles,
        ignore_index=True,
    )

    return resumen, detalle_total