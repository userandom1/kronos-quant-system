from __future__ import annotations

import sys
from pathlib import Path

from motor_mercado.forecast_universal import (
    construir_ensemble_simple,
    ejecutar_forecast,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "forecast_universal"
)


def main() -> None:
    """Ejecuta Forecast Engine Universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_mercado.ejecutar_forecast "
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

    resultados = ejecutar_forecast(
        simbolo=simbolo,
        horizonte=horizonte,
    )

    ensemble = construir_ensemble_simple(
        resultados
    )

    print(
        "=" * 90
    )

    print(
        "FORECAST ENGINE UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        f"Activo              : {simbolo}"
    )

    print(
        f"Horizonte           : "
        f"{horizonte} sesiones"
    )

    print()

    for _, fila in resultados.iterrows():
        print(
            f"{fila['modelo']:<12} | "
            f"Retorno: "
            f"{fila['retorno_estimado'] * 100:+.2f}% | "
            f"Precio: "
            f"{fila['precio_estimado']:,.4f}"
        )

    print()

    print(
        "ENSEMBLE SIMPLE"
    )

    print(
        f"Retorno estimado    : "
        f"{ensemble['retorno_estimado'] * 100:+.2f}%"
    )

    print(
        f"Precio estimado     : "
        f"{ensemble['precio_estimado']:,.4f}"
    )

    print(
        f"Dispersión modelos  : "
        f"{ensemble['dispersion_modelos'] * 100:.2f}%"
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    simbolo_archivo = (
        simbolo
        .replace(
            "=",
            "_",
        )
        .replace(
            "^",
            "",
        )
    )

    ruta = (
        RUTA_RESULTADOS
        / f"{simbolo_archivo}_{horizonte}d.csv"
    )

    resultados.to_csv(
        ruta,
        index=False,
    )

    print()
    print(
        f"Resultado           : {ruta}"
    )


if __name__ == "__main__":
    main()