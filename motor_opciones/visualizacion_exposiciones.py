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
    / "exposiciones_contratos.csv"
)

RUTA_SALIDA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "graficos"
)


METRICAS = {
    "gex": (
        "gex_1pct_dealer",
        "Gamma Exposure - 1% Spot Move",
    ),
    "dex": (
        "dex_dealer",
        "Delta Exposure",
    ),
    "vanna": (
        "vanna_exposure_1pt_dealer",
        "Vanna Exposure - 1 IV Point",
    ),
    "charm": (
        "charm_exposure_dia_dealer",
        "Charm / Delta Decay Exposure diario",
    ),
    "vega": (
        "vega_exposure_1pt_dealer",
        "Vega Exposure - 1 IV Point",
    ),
    "theta": (
        "theta_exposure_dia_dealer",
        "Theta Exposure diario",
    ),
}


def agregar_malla(
    datos: pd.DataFrame,
    columna: str,
) -> pd.DataFrame:
    """Agrega exposure por strike y DTE."""

    return (
        datos.groupby(
            [
                "dte",
                "strike",
            ],
            as_index=False,
        )[columna]
        .sum()
    )


def crear_superficie(
    datos: pd.DataFrame,
    columna: str,
    titulo: str,
) -> go.Figure:
    """Genera una superficie real strike x DTE."""

    agregado = agregar_malla(
        datos,
        columna,
    )

    pivot = agregado.pivot(
        index="dte",
        columns="strike",
        values=columna,
    )

    figura = go.Figure(
        data=[
            go.Surface(
                x=pivot.columns,
                y=pivot.index,
                z=pivot.values,
                connectgaps=False,
                hovertemplate=(
                    "Strike: %{x:.2f}<br>"
                    "DTE: %{y:.2f}<br>"
                    "Exposure: %{z:,.0f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.update_layout(
        title=titulo,
        scene={
            "xaxis_title": "Strike",
            "yaxis_title": "DTE",
            "zaxis_title": "Exposure",
        },
        width=1300,
        height=850,
    )

    return figura


def crear_por_strike(
    datos: pd.DataFrame,
    columna: str,
    titulo: str,
) -> go.Figure:
    """Genera exposición neta agregada por strike."""

    agregado = (
        datos.groupby(
            "strike",
            as_index=False,
        )[columna]
        .sum()
        .sort_values(
            "strike"
        )
    )

    spot = float(
        datos["spot"].iloc[0]
    )

    figura = go.Figure(
        go.Bar(
            x=agregado[
                "strike"
            ],
            y=agregado[
                columna
            ],
            hovertemplate=(
                "Strike: %{x}<br>"
                "Exposure: %{y:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_vline(
        x=spot,
        line_dash="dash",
        annotation_text=(
            f"Spot {spot:.2f}"
        ),
    )

    figura.update_layout(
        title=(
            f"{titulo} - por Strike"
        ),
        xaxis_title="Strike",
        yaxis_title="Exposure",
        width=1300,
        height=700,
    )

    return figura


def crear_indice(
    enlaces: list[
        tuple[str, Path]
    ],
) -> Path:
    """Crea un índice HTML."""

    ruta = (
        RUTA_SALIDA
        / "indice.html"
    )

    contenido = [
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>QQQ Dealer Engine</title>",
        "</head>",
        "<body>",
        "<h1>QQQ Dealer Positioning Engine</h1>",
        "<p>",
        "Las métricas dealer son proxies basados en una convención de posición.",
        "</p>",
        "<ul>",
    ]

    for titulo, archivo in enlaces:
        relativo = archivo.relative_to(
            RUTA_SALIDA
        )

        contenido.append(
            f"<li><a href='{relativo.as_posix()}'>"
            f"{titulo}</a></li>"
        )

    contenido.extend(
        [
            "</ul>",
            "</body>",
            "</html>",
        ]
    )

    ruta.write_text(
        "\n".join(
            contenido
        ),
        encoding="utf-8",
    )

    return ruta


def main() -> None:
    """Genera las visualizaciones del Dealer Engine."""

    RUTA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = pd.read_csv(
        RUTA_DATOS
    )

    enlaces = []

    for nombre, (
        columna,
        titulo,
    ) in METRICAS.items():
        print(
            f"Generando {nombre}..."
        )

        superficie = crear_superficie(
            datos,
            columna,
            titulo,
        )

        ruta_superficie = (
            RUTA_SALIDA
            / f"{nombre}_superficie_3d.html"
        )

        superficie.write_html(
            ruta_superficie
        )

        enlaces.append(
            (
                f"{titulo} - 3D",
                ruta_superficie,
            )
        )

        por_strike = crear_por_strike(
            datos,
            columna,
            titulo,
        )

        ruta_strike = (
            RUTA_SALIDA
            / f"{nombre}_por_strike.html"
        )

        por_strike.write_html(
            ruta_strike
        )

        enlaces.append(
            (
                f"{titulo} - por Strike",
                ruta_strike,
            )
        )

    indice = crear_indice(
        enlaces
    )

    print()
    print(
        "Dashboard generado:"
    )

    print(
        indice
    )

    webbrowser.open(
        indice.as_uri()
    )


if __name__ == "__main__":
    main()