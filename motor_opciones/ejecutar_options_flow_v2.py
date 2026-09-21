from __future__ import annotations

from motor_opciones.options_flow_v2 import (
    RUTA_RESULTADOS,
    agregar_por_strike,
    agregar_por_vencimiento,
    calcular_score,
    cargar_datos,
    construir_resumen,
    preparar_flow,
)


def imprimir_resumen(
    resumen,
    datos,
) -> None:
    """Muestra el resumen principal."""

    fila = resumen.iloc[0]

    print()
    print("=" * 100)
    print("OPTIONS FLOW V2 - QQQ")
    print("=" * 100)

    print(
        f"Contratos activos       : "
        f"{fila['contratos_activos']:,.0f}"
    )

    print(
        f"Nuevo volumen           : "
        f"{fila['nuevo_volumen']:,.0f}"
    )

    print(
        f"Premium nuevo           : "
        f"${fila['premium_nuevo']:,.0f}"
    )

    print(
        f"Premium alcista proxy   : "
        f"${fila['premium_alcista_proxy']:,.0f}"
    )

    print(
        f"Premium bajista proxy   : "
        f"${fila['premium_bajista_proxy']:,.0f}"
    )

    print(
        f"Balance flow proxy      : "
        f"{fila['balance_flow_proxy']:+.3f}"
    )

    print(
        f"Estado                  : "
        f"{fila['estado_flow']}"
    )

    print()
    print("TOP FLOW V2")
    print("-" * 100)

    columnas = [
        "contractSymbol",
        "tipo_t1",
        "vencimiento_t1",
        "strike_t1",
        "nuevo_volumen",
        "nuevo_premium_proxy",
        "ejecucion_proxy",
        "sesgo_proxy",
        "delta_iv_puntos",
        "delta_gex_proxy",
        "flow_score_v2",
    ]

    top = (
        datos
        .sort_values(
            "flow_score_v2",
            ascending=False,
        )
        .head(20)
    )

    print(
        top[
            columnas
        ].to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta Options Flow V2."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_datos()

    datos = preparar_flow(
        datos
    )

    datos = calcular_score(
        datos
    )

    resumen = construir_resumen(
        datos
    )

    strikes = agregar_por_strike(
        datos
    )

    vencimientos = (
        agregar_por_vencimiento(
            datos
        )
    )

    datos.to_csv(
        RUTA_RESULTADOS
        / "options_flow_v2_contratos.csv",
        index=False,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "resumen_flow_v2.csv",
        index=False,
    )

    strikes.to_csv(
        RUTA_RESULTADOS
        / "flow_por_strike.csv",
        index=False,
    )

    vencimientos.to_csv(
        RUTA_RESULTADOS
        / "flow_por_vencimiento.csv",
        index=False,
    )

    imprimir_resumen(
        resumen,
        datos,
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()