from __future__ import annotations

from motor_opciones.dealer_v4 import (
    RUTA_RESULTADOS,
    agregar_flow_por_strike,
    calcular_flow_dealer,
    calcular_niveles,
    cargar_cadena,
    cargar_flow,
    construir_perfil_estructural,
    construir_resumen,
)


def imprimir_resumen(
    resumen,
) -> None:
    """Muestra resultados principales."""

    fila = resumen.iloc[0]

    print()
    print("=" * 100)
    print("DEALER ENGINE V4 - QQQ")
    print("=" * 100)

    print(
        f"Spot                    : "
        f"{fila['spot']:,.2f}"
    )

    print(
        f"GEX estructural         : "
        f"${fila['gex_estructural']:,.0f}"
    )

    print(
        f"DEX estructural         : "
        f"${fila['dex_estructural']:,.0f}"
    )

    print(
        f"Vanna estructural       : "
        f"${fila['vanna_estructural']:,.0f}"
    )

    print(
        f"Charm estructural       : "
        f"${fila['charm_estructural']:,.0f}"
    )

    print()

    flip = fila[
        "gamma_flip"
    ]

    print(
        f"Gamma Flip              : "
        f"{flip:,.2f}"
        if flip is not None
        else "Gamma Flip              : N/D"
    )

    print()

    print(
        f"Gamma Node +            : "
        f"{fila['gamma_node_positivo']}"
    )

    print(
        f"Gamma Node -            : "
        f"{fila['gamma_node_negativo']}"
    )

    print(
        f"Flow Gamma Node         : "
        f"{fila['flow_gamma_node']}"
    )

    print(
        f"Flow Premium Node       : "
        f"{fila['flow_premium_node']}"
    )

    print()
    print("FLOW DINÁMICO DEALER")
    print("-" * 100)

    print(
        f"Delta Flow Proxy        : "
        f"${fila['delta_flow_proxy']:,.0f}"
    )

    print(
        f"Gamma Flow Proxy        : "
        f"${fila['gamma_flow_proxy']:,.0f}"
    )

    print(
        f"Vanna Flow Proxy        : "
        f"${fila['vanna_flow_proxy']:,.0f}"
    )

    print(
        f"Charm Flow Proxy        : "
        f"${fila['charm_flow_proxy']:,.0f}"
    )


def main() -> None:
    """Ejecuta Dealer Engine V4."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Cargando cadena estructural..."
    )

    cadena = cargar_cadena()

    print(
        "Cargando Options Flow V2..."
    )

    flow = cargar_flow()

    print(
        "Calculando perfil estructural..."
    )

    perfil = construir_perfil_estructural(
        cadena
    )

    print(
        "Calculando flow dealer..."
    )

    flow_dealer = calcular_flow_dealer(
        flow
    )

    flow_strike = agregar_flow_por_strike(
        flow_dealer
    )

    niveles = calcular_niveles(
        cadena,
        flow_strike,
    )

    resumen = construir_resumen(
        perfil,
        flow_dealer,
        niveles,
    )

    perfil.to_csv(
        RUTA_RESULTADOS
        / "perfil_gamma_v4.csv",
        index=False,
    )

    flow_dealer.to_csv(
        RUTA_RESULTADOS
        / "dealer_flow_v4.csv",
        index=False,
    )

    flow_strike.to_csv(
        RUTA_RESULTADOS
        / "dealer_flow_por_strike.csv",
        index=False,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "resumen_dealer_v4.csv",
        index=False,
    )

    imprimir_resumen(
        resumen
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()