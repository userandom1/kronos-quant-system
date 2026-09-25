from __future__ import annotations

import sys
from pathlib import Path

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from core.modelos.registro_modelos import (
    listar_modelos,
)
from motor_mercado.ensemble_validado import (
    ejecutar_ensemble_validado,
)
from motor_mercado.seleccion_modelos import (
    seleccionar_mejor_modelo,
)
from motor_validacion.benchmark_forecast_universal import (
    ejecutar_benchmark,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "benchmark_forecast"
)


def main() -> None:
    """Ejecuta benchmark y ensemble universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_mercado.ejecutar_benchmark_forecast "
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

    modelos = listar_modelos()

    print(
        f"Modelos: {modelos}"
    )

    resumen, detalle = ejecutar_benchmark(
        activo=activo,
        datos=datos,
        modelos=modelos,
        horizonte=horizonte,
        pasos=6,
        salto=horizonte,
    )

    mejor_modelo = (
        seleccionar_mejor_modelo(
            resumen
        )
    )

    ensemble = (
        ejecutar_ensemble_validado(
            simbolo=simbolo,
            benchmark=resumen,
            horizonte=horizonte,
        )
    )

    print()
    print(
        "=" * 90
    )
    print(
        "BENCHMARK FORECAST UNIVERSAL"
    )
    print(
        "=" * 90
    )

    print(
        resumen.to_string(
            index=False
        )
    )

    print()
    print(
        f"Mejor modelo      : "
        f"{mejor_modelo}"
    )

    print(
        f"Ensemble retorno  : "
        f"{ensemble['retorno_estimado'] * 100:+.2f}%"
    )

    print(
        f"Ensemble precio   : "
        f"{ensemble['precio_estimado']:,.4f}"
    )

    print(
        f"Pesos             : "
        f"{ensemble['pesos']}"
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

    resumen.to_csv(
        RUTA_RESULTADOS
        / (
            f"{simbolo_archivo}"
            f"_{horizonte}d_resumen.csv"
        ),
        index=False,
    )

    detalle.to_csv(
        RUTA_RESULTADOS
        / (
            f"{simbolo_archivo}"
            f"_{horizonte}d_detalle.csv"
        ),
        index=False,
    )


if __name__ == "__main__":
    main()