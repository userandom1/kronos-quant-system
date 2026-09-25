from __future__ import annotations

import sys

from core.activos import resolver_activo
from motor_mercado.analisis_universal import (
    analizar_activo_universal,
)
from motor_mercado.clasificacion_regimen import (
    clasificar_regimen,
)
from motor_mercado.componentes_regimen import (
    construir_componentes,
)


def analizar_regimen_universal(
    simbolo: str,
) -> dict[str, object]:
    """Calcula el régimen universal de un activo."""

    activo = resolver_activo(
        simbolo
    )

    analisis = analizar_activo_universal(
        activo
    )

    componentes = construir_componentes(
        analisis
    )

    regimen = clasificar_regimen(
        componentes
    )

    analisis["regimen_global"] = (
        regimen.estado
    )

    analisis["score_regimen"] = (
        regimen.puntuacion
    )

    analisis["confianza_regimen"] = (
        regimen.confianza
    )

    analisis["componentes_regimen"] = {
        componente.nombre: {
            "estado": componente.estado,
            "puntuacion": (
                componente.puntuacion
            ),
            "peso": componente.peso,
            "contribucion": (
                componente.contribucion
            ),
        }
        for componente in componentes
    }

    return analisis


def imprimir_regimen(
    resultado: dict[str, object],
) -> None:
    """Imprime el resultado del régimen."""

    print("=" * 90)
    print("MARKET REGIME UNIVERSAL")
    print("=" * 90)

    print(
        f"Activo              : "
        f"{resultado['simbolo']}"
    )

    print(
        f"Clase               : "
        f"{resultado['clase']}"
    )

    print(
        f"Benchmark           : "
        f"{resultado['benchmark']}"
    )

    print(
        f"Precio              : "
        f"{resultado['precio']:,.4f}"
    )

    print()

    print(
        f"Régimen             : "
        f"{resultado['regimen_global']}"
    )

    print(
        f"Score               : "
        f"{resultado['score_regimen']:+.4f}"
    )

    print(
        f"Confianza           : "
        f"{resultado['confianza_regimen']}"
    )

    print()

    print("-" * 90)
    print("COMPONENTES")
    print("-" * 90)

    componentes = resultado[
        "componentes_regimen"
    ]

    for nombre, componente in componentes.items():
        print(
            f"{nombre:<15} | "
            f"{componente['estado']:<20} | "
            f"Score: "
            f"{componente['puntuacion']:+.3f} | "
            f"Peso: "
            f"{componente['peso']:.2f} | "
            f"Contribución: "
            f"{componente['contribucion']:+.3f}"
        )

    print()

    print("-" * 90)
    print("MÉTRICAS")
    print("-" * 90)

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
        f"Drawdown actual     : "
        f"{resultado['drawdown_actual'] * 100:.2f}%"
    )

    print(
        f"Sharpe 60D          : "
        f"{resultado['sharpe60']:.3f}"
    )

    print(
        f"Beta 60D            : "
        f"{resultado['beta60']}"
    )

    print(
        f"Correlación 60D     : "
        f"{resultado['correlacion60']}"
    )


def main() -> None:
    """Ejecuta Market Regime Universal desde terminal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_mercado.regimen_universal SYMBOL"
        )

    simbolo = sys.argv[
        1
    ]

    resultado = analizar_regimen_universal(
        simbolo
    )

    imprimir_regimen(
        resultado
    )


if __name__ == "__main__":
    main()