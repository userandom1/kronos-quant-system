from __future__ import annotations

import pandas as pd

from motor_opciones.options_flow_universal import (
    comparar_snapshots,
    resumir_flow,
)


def main() -> None:
    """Prueba Options Flow con snapshots sintéticos."""

    anterior = pd.DataFrame(
        {
            "contract_symbol": [
                "CALL_100",
                "PUT_100",
            ],
            "tipo_opcion": [
                "CALL",
                "PUT",
            ],
            "volumen": [
                100,
                80,
            ],
            "open_interest": [
                1000,
                900,
            ],
            "bid": [
                2.00,
                1.90,
            ],
            "ask": [
                2.10,
                2.00,
            ],
            "ultimo": [
                2.05,
                1.95,
            ],
            "iv": [
                0.25,
                0.27,
            ],
        }
    )

    actual = anterior.copy()

    actual[
        "volumen"
    ] = [
        180,
        150,
    ]

    actual[
        "open_interest"
    ] = [
        1030,
        940,
    ]

    actual[
        "ultimo"
    ] = [
        2.10,
        2.00,
    ]

    flujo = comparar_snapshots(
        anterior,
        actual,
    )

    resumen = resumir_flow(
        flujo
    )

    assert flujo[
        "delta_volumen"
    ].sum() == 150

    assert resumen[
        "nuevo_volumen"
    ] == 150

    print(
        "OPTIONS FLOW UNIVERSAL: OK"
    )

    print(
        resumen
    )


if __name__ == "__main__":
    main()