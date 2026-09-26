from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from motor_mercado.analisis_universal import (
    analizar_activo_universal,
)
from motor_mercado.forecast_universal import (
    ejecutar_forecast,
)
from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
)
from motor_opciones.cadena_opciones import (
    enriquecer_cadena,
)
from motor_opciones.dealer_universal import (
    calcular_exposiciones_dealer,
    resumir_dealer,
)
from motor_opciones.escenarios_opciones import (
    generar_graficas_escenarios,
)
from motor_opciones.graficas_avanzadas import (
    generar_pack_graficas,
)
from motor_opciones.griegas_universales import (
    aplicar_griegas,
)
from motor_opciones.indice_graficas import (
    generar_indice_graficas,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "deep_research"
)


def limpiar_simbolo(
    simbolo: str,
) -> str:
    """Normaliza ticker para utilizarlo como carpeta."""

    return (
        simbolo
        .replace(
            "=",
            "_",
        )
        .replace(
            "^",
            "",
        )
        .replace(
            "/",
            "_",
        )
    )


def obtener_cadena_multi_vencimiento(
    simbolo: str,
    numero_vencimientos: int = 12,
) -> tuple[pd.DataFrame, float]:
    """Obtiene varios vencimientos para análisis 3D."""

    activo = resolver_activo(
        simbolo
    )

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    spot = proveedor.obtener_precio_actual(
        activo
    )

    vencimientos = (
        proveedor
        .listar_vencimientos_opciones(
            activo
        )
    )

    if not vencimientos:
        raise RuntimeError(
            f"No existen vencimientos "
            f"para {simbolo}."
        )

    seleccionados = vencimientos[
        :numero_vencimientos
    ]

    cadenas = []

    for vencimiento in seleccionados:
        print(
            f"  Opciones "
            f"{simbolo} "
            f"{vencimiento}..."
        )

        try:
            cadena = (
                proveedor
                .obtener_cadena_opciones(
                    activo=activo,
                    vencimiento=vencimiento,
                )
            )

            if cadena.empty:
                continue

            cadena = enriquecer_cadena(
                cadena=cadena,
                spot=spot,
            )

            cadena = aplicar_griegas(
                cadena=cadena,
                spot=spot,
            )

            cadena = (
                calcular_exposiciones_dealer(
                    cadena=cadena,
                    spot=spot,
                )
            )

            cadenas.append(
                cadena
            )

        except Exception as error:
            print(
                f"    ERROR: {error}"
            )

    if not cadenas:
        raise RuntimeError(
            "No se obtuvo ninguna "
            "cadena válida."
        )

    return (
        pd.concat(
            cadenas,
            ignore_index=True,
        ),
        spot,
    )


def ejecutar_deep_research_activo(
    ticker: str,
    horizonte: int = 20,
    numero_vencimientos: int = 12,
    dte_escenarios: int = 35,
) -> dict[str, Any]:
    """Ejecuta Deep Research Universal."""

    ticker = (
        ticker
        .strip()
        .upper()
    )

    activo = resolver_activo(
        ticker
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    ruta_resultado = (
        RUTA_RESULTADOS
        / limpiar_simbolo(
            ticker
        )
        / timestamp
    )

    ruta_graficas = (
        ruta_resultado
        / "graficas"
    )

    ruta_resultado.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "=" * 90
    )

    print(
        f"DEEP RESEARCH — {ticker}"
    )

    print(
        "=" * 90
    )

    print(
        "1/6 Market Intelligence..."
    )

    mercado = analizar_activo_universal(
        activo
    )

    regimen = analizar_regimen_universal(
        ticker
    )

    print(
        "2/6 Forecast Engine..."
    )

    forecasts = {}

    for horizonte_forecast in [
        5,
        20,
        60,
    ]:
        try:
            resultado_forecast = (
                ejecutar_forecast(
                    simbolo=ticker,
                    horizonte=(
                        horizonte_forecast
                    ),
                )
            )

            forecasts[
                str(
                    horizonte_forecast
                )
            ] = (
                resultado_forecast
                .to_dict(
                    orient="records"
                )
            )

            resultado_forecast.to_csv(
                ruta_resultado
                / (
                    f"forecast_"
                    f"{horizonte_forecast}d.csv"
                ),
                index=False,
            )

        except Exception as error:
            print(
                f"  Forecast "
                f"{horizonte_forecast}D: "
                f"ERROR {error}"
            )

    cadena = None
    spot = None
    dealer = {}
    graficas = {}

    if activo.capacidades.opciones:
        print(
            "3/6 Options + Greeks..."
        )

        try:
            cadena, spot = (
                obtener_cadena_multi_vencimiento(
                    simbolo=ticker,
                    numero_vencimientos=(
                        numero_vencimientos
                    ),
                )
            )

            cadena.to_csv(
                ruta_resultado
                / "cadena_opciones.csv",
                index=False,
            )

            print(
                "4/6 Dealer Engine..."
            )

            dealer = resumir_dealer(
                cadena
            )

            pd.DataFrame(
                [
                    dealer
                ]
            ).to_csv(
                ruta_resultado
                / "dealer.csv",
                index=False,
            )

            print(
                "5/6 Gráficas "
                "Greeks/Dealer..."
            )

            graficas_base = (
                generar_pack_graficas(
                    ticker=ticker,
                    cadena=cadena,
                    spot=spot,
                    ruta_base=(
                        ruta_graficas
                    ),
                )
            )

            graficas.update(
                graficas_base
            )

            print(
                "6/6 Scenario Engine..."
            )

            graficas_escenarios = (
                generar_graficas_escenarios(
                    ticker=ticker,
                    cadena=cadena,
                    spot=spot,
                    ruta_base=(
                        ruta_graficas
                    ),
                    dte_objetivo=(
                        dte_escenarios
                    ),
                )
            )

            graficas.update(
                graficas_escenarios
            )

            indice = generar_indice_graficas(
                ticker=ticker,
                graficas=graficas,
                ruta_salida=(
                    ruta_graficas
                    / "indice_graficas.html"
                ),
            )

            graficas[
                "indice_graficas"
            ] = str(
                indice
            )

        except Exception as error:
            print(
                f"  Options/Gráficas: "
                f"ERROR {error}"
            )

    else:
        print(
            "3/6 Options: "
            "NO_COMPATIBLE"
        )

    pd.DataFrame(
        [
            mercado
        ]
    ).to_csv(
        ruta_resultado
        / "mercado.csv",
        index=False,
    )

    regimen_simple = {
        clave: valor
        for clave, valor
        in regimen.items()
        if clave
        != "componentes_regimen"
    }

    pd.DataFrame(
        [
            regimen_simple
        ]
    ).to_csv(
        ruta_resultado
        / "regimen.csv",
        index=False,
    )

    resumen = {
        "ticker": ticker,
        "clase": activo.clase.value,
        "spot": (
            spot
            if spot is not None
            else mercado.get(
                "precio"
            )
        ),
        "regimen": regimen.get(
            "regimen_global"
        ),
        "score_regimen": regimen.get(
            "score_regimen"
        ),
        "retorno_20d": mercado.get(
            "retorno_20d"
        ),
        "retorno_60d": mercado.get(
            "retorno_60d"
        ),
        "vol20": mercado.get(
            "vol20"
        ),
        "vol60": mercado.get(
            "vol60"
        ),
        "drawdown_actual": mercado.get(
            "drawdown_actual"
        ),
        "beta": mercado.get(
            "beta"
        ),
        "graficas_generadas": len(
            graficas
        ),
        "ruta": str(
            ruta_resultado
        ),
    }

    for clave, valor in dealer.items():
        resumen[
            f"dealer_{clave}"
        ] = valor

    pd.DataFrame(
        [
            resumen
        ]
    ).to_csv(
        ruta_resultado
        / "resumen.csv",
        index=False,
    )

    pd.DataFrame(
        [
            {
                "grafica": nombre,
                "ruta": ruta,
            }
            for nombre, ruta
            in graficas.items()
        ]
    ).to_csv(
        ruta_resultado
        / "indice_graficas.csv",
        index=False,
    )

    print()
    print(
        "=" * 90
    )

    print(
        "DEEP RESEARCH COMPLETADO"
    )

    print(
        "=" * 90
    )

    print(
        f"Activo             : "
        f"{ticker}"
    )

    print(
        f"Clase              : "
        f"{activo.clase.value}"
    )

    print(
        f"Régimen            : "
        f"{regimen.get('regimen_global')}"
    )

    print(
        f"Score régimen      : "
        f"{regimen.get('score_regimen')}"
    )

    print(
        f"Gráficas           : "
        f"{len(graficas)}"
    )

    if dealer:
        print(
            f"Net GEX            : "
            f"{dealer.get('net_gex_1pct', 0):,.0f}"
        )

        print(
            f"Net DEX            : "
            f"{dealer.get('net_dex', 0):,.0f}"
        )

        print(
            f"Call Wall          : "
            f"{dealer.get('call_wall')}"
        )

        print(
            f"Put Wall           : "
            f"{dealer.get('put_wall')}"
        )

    print(
        f"Resultados         : "
        f"{ruta_resultado}"
    )

    if graficas:
        print(
            f"Índice gráficas    : "
            f"{ruta_graficas / 'indice_graficas.html'}"
        )

    return {
        "ticker": ticker,
        "ruta_resultados": str(
            ruta_resultado
        ),
        "resumen": resumen,
        "mercado": mercado,
        "regimen": regimen,
        "forecast": forecasts,
        "dealer": dealer,
        "graficas": graficas,
    }