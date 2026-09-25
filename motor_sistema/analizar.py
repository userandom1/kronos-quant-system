from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from motor_sistema.orquestador_universal import (
    analizar_activo_completo,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "sistema_universal"
)


def limpiar_simbolo(
    simbolo: str,
) -> str:
    """Limpia el símbolo para utilizarlo en archivos."""

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


def imprimir_resultado(
    resultado,
) -> None:
    """Imprime resumen del análisis completo."""

    print(
        "=" * 90
    )

    print(
        "QUANT PLATFORM — ANÁLISIS UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        f"Activo             : "
        f"{resultado.simbolo}"
    )

    print(
        f"Clase              : "
        f"{resultado.clase}"
    )

    print()

    for nombre, motor in resultado.motores.items():
        print(
            f"{nombre:<20}: "
            f"{motor.estado}"
        )

        if motor.error:
            print(
                f"  Error            : "
                f"{motor.error}"
            )

    mercado = resultado.motores.get(
        "market_regime"
    )

    if (
        mercado
        and mercado.estado == "OK"
    ):
        print()
        print(
            f"Régimen            : "
            f"{mercado.datos.get('regimen_global')}"
        )

        print(
            f"Score régimen      : "
            f"{mercado.datos.get('score_regimen'):+.3f}"
        )

    forecast = resultado.motores.get(
        "forecast"
    )

    if (
        forecast
        and forecast.estado == "OK"
    ):
        ensemble = forecast.datos[
            "ensemble"
        ]

        print()
        print(
            f"Forecast retorno   : "
            f"{ensemble['retorno_estimado'] * 100:+.2f}%"
        )

        print(
            f"Forecast precio    : "
            f"{ensemble['precio_estimado']:,.4f}"
        )

    opciones = resultado.motores.get(
        "opciones"
    )

    if (
        opciones
        and opciones.estado == "OK"
    ):
        dealer = opciones.datos[
            "dealer"
        ]

        print()
        print(
            f"Opciones contratos : "
            f"{opciones.datos['contratos']:,}"
        )

        print(
            f"Net GEX 1%         : "
            f"${dealer['net_gex_1pct']:,.0f}"
        )

        print(
            f"Call Wall          : "
            f"{dealer['call_wall']}"
        )

        print(
            f"Put Wall           : "
            f"{dealer['put_wall']}"
        )


def guardar_resultado(
    resultado,
) -> Path:
    """Guarda el resultado en JSON."""

    ruta_activo = (
        RUTA_RESULTADOS
        / limpiar_simbolo(
            resultado.simbolo
        )
    )

    ruta_activo.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    archivo = (
        ruta_activo
        / f"analisis_{timestamp}.json"
    )

    datos = asdict(
        resultado
    )

    datos[
        "timestamp"
    ] = resultado.timestamp.isoformat()

    with archivo.open(
        "w",
        encoding="utf-8",
    ) as fichero:
        json.dump(
            datos,
            fichero,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    return archivo


def main() -> None:
    """Punto de entrada universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_sistema.analizar "
            "ACTIVO [HORIZONTE]"
        )

    simbolo = sys.argv[
        1
    ].upper()

    horizonte = (
        int(
            sys.argv[2]
        )
        if len(sys.argv) >= 3
        else 20
    )

    resultado = analizar_activo_completo(
        simbolo=simbolo,
        horizonte_forecast=horizonte,
    )

    imprimir_resultado(
        resultado
    )

    archivo = guardar_resultado(
        resultado
    )

    print()
    print(
        f"Resultado guardado : {archivo}"
    )


if __name__ == "__main__":
    main()