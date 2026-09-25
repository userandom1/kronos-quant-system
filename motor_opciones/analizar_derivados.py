from __future__ import annotations

import sys

import pandas as pd

from core.activos import resolver_activo
from motor_opciones.dealer_universal import (
    calcular_exposiciones_dealer,
    resumir_dealer,
)
from motor_opciones.griegas_universales import (
    aplicar_griegas,
)
from motor_opciones.options_engine_universal import (
    ejecutar_options_engine,
)
from motor_opciones.options_flow_universal import (
    comparar_snapshots,
    resumir_flow,
)
from motor_opciones.snapshot_opciones import (
    guardar_snapshot,
    obtener_ultimos_snapshots,
)


def main() -> None:
    """Ejecuta análisis universal de derivados."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_opciones.analizar_derivados "
            "ACTIVO"
        )

    simbolo = sys.argv[
        1
    ].upper()

    activo = resolver_activo(
        simbolo
    )

    resultado = ejecutar_options_engine(
        activo
    )

    cadena = aplicar_griegas(
        cadena=resultado.cadena,
        spot=resultado.spot,
    )

    cadena = calcular_exposiciones_dealer(
        cadena=cadena,
        spot=resultado.spot,
    )

    dealer = resumir_dealer(
        cadena
    )

    snapshots_anteriores = (
        obtener_ultimos_snapshots(
            simbolo,
            cantidad=1,
        )
    )

    archivo_actual = guardar_snapshot(
        simbolo,
        cadena,
    )

    print(
        "=" * 90
    )

    print(
        "DERIVATIVES ENGINE UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        f"Activo            : {simbolo}"
    )

    print(
        f"Spot              : "
        f"{resultado.spot:,.4f}"
    )

    print(
        f"Vencimiento       : "
        f"{resultado.vencimiento}"
    )

    print(
        f"Contratos         : "
        f"{len(cadena):,}"
    )

    print()

    print(
        f"Net GEX 1%        : "
        f"${dealer['net_gex_1pct']:,.0f}"
    )

    print(
        f"Net DEX           : "
        f"${dealer['net_dex']:,.0f}"
    )

    print(
        f"Net Vanna 1pt     : "
        f"${dealer['net_vanna_1pt']:,.0f}"
    )

    print(
        f"Net Charm día     : "
        f"${dealer['net_charm_dia']:,.0f}"
    )

    print(
        f"Gamma Node +      : "
        f"{dealer['gamma_node_positivo']}"
    )

    print(
        f"Gamma Node -      : "
        f"{dealer['gamma_node_negativo']}"
    )

    print(
        f"Call Wall         : "
        f"{dealer['call_wall']}"
    )

    print(
        f"Put Wall          : "
        f"{dealer['put_wall']}"
    )

    if snapshots_anteriores:
        anterior = pd.read_csv(
            snapshots_anteriores[0]
        )

        actual = pd.read_csv(
            archivo_actual
        )

        flujo = comparar_snapshots(
            anterior,
            actual,
        )

        resumen_flow = resumir_flow(
            flujo
        )

        print()
        print(
            "OPTIONS FLOW"
        )

        print(
            f"Estado            : "
            f"{resumen_flow['estado']}"
        )

        print(
            f"Balance           : "
            f"{resumen_flow['balance']:+.3f}"
        )

        print(
            f"Premium alcista   : "
            f"${resumen_flow['premium_alcista']:,.0f}"
        )

        print(
            f"Premium bajista   : "
            f"${resumen_flow['premium_bajista']:,.0f}"
        )

    else:
        print()
        print(
            "Options Flow      : "
            "primer snapshot capturado"
        )

    print()
    print(
        f"Snapshot          : "
        f"{archivo_actual}"
    )


if __name__ == "__main__":
    main()