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
    / "intradia_v3"
)

RUTA_GRAFICOS = (
    RUTA_DATOS
    / "graficos"
)


def cargar(
    archivo: str,
) -> pd.DataFrame:
    """Carga un CSV del motor V3."""

    return pd.read_csv(
        RUTA_DATOS
        / archivo
    )


def perfil_gamma_total(
    datos: pd.DataFrame,
) -> go.Figure:
    """Gráfico del Gamma Profile total."""

    figura = go.Figure()

    figura.add_trace(
        go.Scatter(
            x=datos["spot"],
            y=datos[
                "net_gex_1pct"
            ],
            mode="lines",
            name="Net GEX",
        )
    )

    figura.add_hline(
        y=0,
        line_dash="dash",
    )

    figura.update_layout(
        title=(
            "QQQ - Gamma Profile intradía"
        ),
        xaxis_title="QQQ Spot",
        yaxis_title="Net GEX por 1% move",
        width=1250,
        height=700,
    )

    return figura


def perfil_gamma_bandas(
    datos: pd.DataFrame,
) -> go.Figure:
    """Compara Gamma por horizonte de vencimiento."""

    figura = go.Figure()

    for banda in datos[
        "banda_dte"
    ].unique():
        muestra = datos[
            datos[
                "banda_dte"
            ]
            == banda
        ]

        figura.add_trace(
            go.Scatter(
                x=muestra["spot"],
                y=muestra[
                    "net_gex_1pct"
                ],
                mode="lines",
                name=banda,
            )
        )

    figura.add_hline(
        y=0,
        line_dash="dash",
    )

    figura.update_layout(
        title=(
            "QQQ - Gamma Profile por DTE"
        ),
        xaxis_title="QQQ Spot",
        yaxis_title="Net GEX",
        width=1250,
        height=750,
    )

    return figura


def crear_superficie(
    datos: pd.DataFrame,
    columna: str,
    titulo: str,
) -> go.Figure:
    """Crea una superficie Spot x IV."""

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
                    "IV: %{y:+.1f} pt<br>"
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
                "Shock IV ATM"
            ),
            "zaxis_title": "Exposure",
        },
        width=1300,
        height=850,
    )

    return figura


def crear_superficie_skew(
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea Spot x skew para Net GEX."""

    pivot = datos.pivot(
        index="shock_skew",
        columns="spot",
        values="net_gex_1pct",
    )

    figura = go.Figure(
        data=[
            go.Surface(
                x=pivot.columns,
                y=pivot.index,
                z=pivot.values,
                hovertemplate=(
                    "Spot: %{x:.2f}<br>"
                    "Skew shock: %{y:+.3f}<br>"
                    "Net GEX: %{z:,.0f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.update_layout(
        title=(
            "QQQ - Net GEX: Spot x Skew"
        ),
        scene={
            "xaxis_title": "QQQ Spot",
            "yaxis_title": "Shock de skew",
            "zaxis_title": "Net GEX",
        },
        width=1300,
        height=850,
    )

    return figura


def crear_flujo_intradía(
    datos: pd.DataFrame,
) -> go.Figure:
    """Muestra hedge flow puro provocado por Spot."""

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
                "flujo_hedge_total"
            ],
            name="Hedge Flow",
        )
    )

    figura.add_hline(
        y=0,
        line_dash="dash",
    )

    figura.update_layout(
        title=(
            "QQQ - Dealer Hedge Flow intradía"
        ),
        xaxis_title="QQQ Spot",
        yaxis_title=(
            "Cambio estimado del hedge ($)"
        ),
        width=1250,
        height=700,
    )

    return figura


def crear_indice(
    enlaces: list[
        tuple[str, Path]
    ],
) -> Path:
    """Construye el índice del dashboard."""

    ruta = (
        RUTA_GRAFICOS
        / "indice.html"
    )

    html = [
        "<!DOCTYPE html>",
        "<html lang='es'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>Dealer Engine V3</title>",
        "<style>",
        "body {",
        "font-family: Arial, sans-serif;",
        "max-width: 1200px;",
        "margin: 40px auto;",
        "padding: 0 20px;",
        "}",
        "h1 { margin-bottom: 10px; }",
        "li { margin: 10px 0; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>QQQ Dealer Scenario Engine V3</h1>",
        "<p>",
        "Análisis intradía de Gamma, IV, Skew, Vanna, Charm y hedge flow.",
        "</p>",
        "<p>",
        "<strong>Advertencia:</strong> las posiciones dealer son proxies.",
        "</p>",
        "<ul>",
    ]

    for titulo, archivo in enlaces:
        relativo = archivo.relative_to(
            RUTA_GRAFICOS
        )

        html.append(
            f"<li><a href='{relativo.as_posix()}'>"
            f"{titulo}</a></li>"
        )

    html.extend(
        [
            "</ul>",
            "</body>",
            "</html>",
        ]
    )

    ruta.write_text(
        "\n".join(
            html
        ),
        encoding="utf-8",
    )

    return ruta


def guardar(
    figura: go.Figure,
    nombre: str,
    titulo: str,
    enlaces: list,
) -> None:
    """Guarda una figura y la añade al índice."""

    ruta = (
        RUTA_GRAFICOS
        / nombre
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


def main() -> None:
    """Genera el dashboard V3."""

    RUTA_GRAFICOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    escenarios = cargar(
        "escenarios_intradia.csv"
    )

    skew = cargar(
        "escenarios_skew.csv"
    )

    gamma_total = cargar(
        "perfil_gamma_total.csv"
    )

    gamma_bandas = cargar(
        "perfil_gamma_bandas.csv"
    )

    enlaces = []

    guardar(
        perfil_gamma_total(
            gamma_total
        ),
        "01_gamma_profile_total.html",
        "Gamma Profile total",
        enlaces,
    )

    guardar(
        perfil_gamma_bandas(
            gamma_bandas
        ),
        "02_gamma_profile_dte.html",
        "Gamma Profile por DTE",
        enlaces,
    )

    guardar(
        crear_flujo_intradía(
            escenarios
        ),
        "03_hedge_flow_intradia.html",
        "Dealer Hedge Flow intradía",
        enlaces,
    )

    guardar(
        crear_superficie(
            escenarios,
            "net_gex_1pct",
            "Net GEX - Spot x IV",
        ),
        "04_gex_spot_iv.html",
        "Net GEX: Spot x IV",
        enlaces,
    )

    guardar(
        crear_superficie(
            escenarios,
            "flujo_hedge_total",
            "Dealer Hedge Flow - Spot x IV",
        ),
        "05_hedge_spot_iv.html",
        "Hedge Flow: Spot x IV",
        enlaces,
    )

    guardar(
        crear_superficie(
            escenarios,
            "net_vanna_1pt",
            "Net Vanna - Spot x IV",
        ),
        "06_vanna_spot_iv.html",
        "Net Vanna: Spot x IV",
        enlaces,
    )

    guardar(
        crear_superficie(
            escenarios,
            "net_charm_dia",
            "Net Charm - Spot x IV",
        ),
        "07_charm_spot_iv.html",
        "Net Charm: Spot x IV",
        enlaces,
    )

    guardar(
        crear_superficie_skew(
            skew
        ),
        "08_gex_spot_skew.html",
        "Net GEX: Spot x Skew",
        enlaces,
    )

    indice = crear_indice(
        enlaces
    )

    print()
    print("=" * 80)
    print("DASHBOARD DEALER ENGINE V3 GENERADO")
    print("=" * 80)

    print(
        indice
    )

    webbrowser.open(
        indice.as_uri()
    )


if __name__ == "__main__":
    main()