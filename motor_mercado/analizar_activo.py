from __future__ import annotations

import sys

from core.activos import resolver_activo
from motor_mercado.analisis_universal import (
    analizar_activo_universal,
)


def imprimir_resultado(
    resultado: dict[str, object],
) -> None:
    """Imprime el análisis universal."""

    print("=" * 90)
    print("ANÁLISIS UNIVERSAL DE ACTIVO")
    print("=" * 90)

    print(
        f"Símbolo             : "
        f"{resultado['simbolo']}"
    )

    print(
        f"Clase               : "
        f"{resultado['clase']}"
    )

    print(
        f"Mercado             : "
        f"{resultado['mercado']}"
    )

    print(
        f"Benchmark           : "
        f"{resultado['benchmark']}"
    )

    print(
        f"Precio              : "
        f"{resultado['precio']:,.4f}"
    )

    print(
        f"Retorno 20D         : "
        f"{resultado['retorno_20d'] * 100:+.2f}%"
    )

    print(
        f"Retorno 60D         : "
        f"{resultado['retorno_60d'] * 100:+.2f}%"
    )

    print(
        f"Volatilidad 20D     : "
        f"{resultado['vol20'] * 100:.2f}%"
    )

    print(
        f"Volatilidad 60D     : "
        f"{resultado['vol60'] * 100:.2f}%"
    )

    print(
        f"Sharpe 20D          : "
        f"{resultado['sharpe20']:.3f}"
    )

    print(
        f"Sharpe 60D          : "
        f"{resultado['sharpe60']:.3f}"
    )

    print(
        f"Drawdown actual     : "
        f"{resultado['drawdown_actual'] * 100:.2f}%"
    )

    print(
        f"Beta 60D            : "
        f"{resultado['beta60']}"
    )

    print(
        f"Correlación 60D     : "
        f"{resultado['correlacion60']}"
    )

    print(
        f"Tendencia           : "
        f"{resultado['regimen_tendencia']}"
    )

    print(
        f"Momentum            : "
        f"{resultado['regimen_momentum']}"
    )

    print(
        f"Volatilidad         : "
        f"{resultado['regimen_volatilidad']}"
    )


def main() -> None:
    """Ejecuta análisis universal desde CLI."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_mercado.analizar_activo SYMBOL"
        )

    simbolo = sys.argv[
        1
    ]

    activo = resolver_activo(
        simbolo
    )

    resultado = analizar_activo_universal(
        activo
    )

    imprimir_resultado(
        resultado
    )


if __name__ == "__main__":
    main()