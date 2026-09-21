from pathlib import Path
import webbrowser

import pandas as pd
import plotly.graph_objects as go


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_DATOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "escenarios_v2"
)

RUTA_GRAFICOS = (
    RUTA_DATOS
    / "graficos"
)


# =============================================================================
# DATOS
# =============================================================================


def cargar_escenarios() -> pd.DataFrame:
    """Carga la matriz de escenarios."""

    return pd.read_csv(
        RUTA_DATOS
        / "escenarios_completos.csv"
    )


# =============================================================================
# PERFIL GAMMA
# =============================================================================


def crear_perfil_gamma(
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea Net GEX frente a Spot."""

    muestra = datos[
        (
            datos[
                "shock_iv_puntos"
            ]
            == 0
        )
        & (
            datos[
                "decaimiento_dias"
            ]
            == 0
        )
    ].sort_values(
        "spot"
    )

    figura = go.Figure()

    figura.add_trace(
        go.Scatter(
            x=muestra["spot"],
            y=muestra[
                "net_gex_1pct"
            ],
            mode="lines+markers",
            name="Net GEX",
            hovertemplate=(
                "Spot: %{x:.2f}<br>"
                "Net GEX: %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_hline(
        y=0,
        line_dash="dash",
    )

    figura.update_layout(
        title="QQQ - Net GEX vs Spot",
        xaxis_title="QQQ Spot",
        yaxis_title=(
            "Net GEX por movimiento del 1%"
        ),
        width=1200,
        height=700,
    )

    return figura


# =============================================================================
# HEDGE FLOW
# =============================================================================


def crear_hedge_flow(
    datos: pd.DataFrame,
) -> go.Figure:
    """Representa el cambio estimado del hedge dealer."""

    muestra = datos[
        (
            datos[
                "shock_iv_puntos"
            ]
            == 0
        )
        & (
            datos[
                "decaimiento_dias"
            ]
            == 0
        )
    ].sort_values(
        "spot"
    )

    figura = go.Figure()

    figura.add_trace(
        go.Bar(
            x=muestra["spot"],
            y=muestra[
                "flujo_hedge_estimado"
            ],
            hovertemplate=(
                "Spot: %{x:.2f}<br>"
                "Hedge flow: %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_hline(
        y=0,
        line_dash="dash",
    )

    figura.update_layout(
        title=(
            "QQQ - Dealer Hedge Flow estimado"
        ),
        xaxis_title="QQQ Spot",
        yaxis_title=(
            "Cambio estimado del hedge ($)"
        ),
        width=1200,
        height=700,
    )

    return figura


# =============================================================================
# SUPERFICIES SPOT x IV
# =============================================================================


def crear_superficie(
    datos: pd.DataFrame,
    columna: str,
    titulo: str,
) -> go.Figure:
    """Crea una superficie Spot x IV para t=0."""

    muestra = datos[
        datos[
            "decaimiento_dias"
        ]
        == 0
    ]

    pivot = muestra.pivot(
        index="shock_iv_puntos",
        columns="spot",
        values=columna,
    )

    figura = go.Figure(
        data=[
            go.Surface(
                x=pivot.columns,
                y=pivot.index,
                z=pivot.values,
                hovertemplate=(
                    "Spot: %{x:.2f}<br>"
                    "IV shock: %{y:+.1f} pt<br>"
                    "Valor: %{z:,.0f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.update_layout(
        title=titulo,
        scene={
            "xaxis_title": "QQQ Spot",
            "yaxis_title": (
                "Shock IV (puntos)"
            ),
            "zaxis_title": "Exposure",
        },
        width=1300,
        height=850,
    )

    return figura


# =============================================================================
# ÍNDICE
# =============================================================================


def crear_indice(
    enlaces: list[
        tuple[str, Path]
    ],
) -> Path:
    """Crea página índice."""

    ruta = (
        RUTA_GRAFICOS
        / "indice.html"
    )

    lineas = [
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>Dealer Scenario Engine V2</title>",
        "</head>",
        "<body>",
        "<h1>Dealer Scenario Engine V2 - QQQ</h1>",
        "<p>",
        "Las exposiciones dealer son proxies, "
        "no posiciones observadas directamente.",
        "</p>",
        "<ul>",
    ]

    for titulo, archivo in enlaces:
        relativo = archivo.relative_to(
            RUTA_GRAFICOS
        )

        lineas.append(
            f"<li><a href='{relativo.as_posix()}'>"
            f"{titulo}</a></li>"
        )

    lineas.extend(
        [
            "</ul>",
            "</body>",
            "</html>",
        ]
    )

    ruta.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8",
    )

    return ruta


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Genera todas las visualizaciones."""

    RUTA_GRAFICOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_escenarios()

    enlaces = []

    perfil_gamma = crear_perfil_gamma(
        datos
    )

    ruta = (
        RUTA_GRAFICOS
        / "perfil_gamma.html"
    )

    perfil_gamma.write_html(
        ruta
    )

    enlaces.append(
        (
            "Net GEX vs Spot",
            ruta,
        )
    )

    hedge = crear_hedge_flow(
        datos
    )

    ruta = (
        RUTA_GRAFICOS
        / "hedge_flow_spot.html"
    )

    hedge.write_html(
        ruta
    )

    enlaces.append(
        (
            "Dealer Hedge Flow vs Spot",
            ruta,
        )
    )

    superficies = {
        "net_gex_1pct": (
            "superficie_gex_spot_iv.html",
            "Net GEX - Spot x IV",
        ),
        "flujo_hedge_estimado": (
            "superficie_hedge_spot_iv.html",
            "Dealer Hedge Flow - Spot x IV",
        ),
        "net_vanna_1pt": (
            "superficie_vanna_spot_iv.html",
            "Net Vanna - Spot x IV",
        ),
        "net_charm_dia": (
            "superficie_charm_spot_iv.html",
            "Net Charm - Spot x IV",
        ),
    }

    for columna, (
        archivo,
        titulo,
    ) in superficies.items():
        figura = crear_superficie(
            datos,
            columna,
            titulo,
        )

        ruta = (
            RUTA_GRAFICOS
            / archivo
        )

        figura.write_html(
            ruta
        )

        enlaces.append(
            (
                titulo,
                ruta,
            )
        )

    indice = crear_indice(
        enlaces
    )

    print()
    print(
        "Dashboard V2 generado:"
    )

    print(
        indice
    )

    webbrowser.open(
        indice.as_uri()
    )


if __name__ == "__main__":
    main()