from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from motor_opciones.superficie_volatilidad import (
    ConfiguracionVolatilidad,
    generar_superficie_volatilidad,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "superficie_volatilidad"
)


def crear_matrices(datos):
    """Convierte la superficie tabular a matrices Plotly."""

    pivot = datos.pivot(
        index="dte",
        columns="log_moneyness",
        values="iv_pct",
    )

    x = pivot.columns.to_numpy(dtype=float)
    y = pivot.index.to_numpy(dtype=float)
    z = pivot.to_numpy(dtype=float)

    return x, y, z


def crear_superficie(datos) -> go.Figure:
    """Genera superficie 3D de volatilidad implícita."""

    x, y, z = crear_matrices(datos)

    figura = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                customdata=np.exp(
                    np.broadcast_to(
                        x,
                        z.shape,
                    )
                ),
                hovertemplate=(
                    "log(K/S): %{x:.4f}<br>"
                    "K/S: %{customdata:.4f}<br>"
                    "DTE: %{y:.2f}<br>"
                    "IV: %{z:.2f}%"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.update_layout(
        title="Volatility Surface sintética",
        scene={
            "xaxis_title": "Log-moneyness ln(K/S)",
            "yaxis_title": "DTE",
            "zaxis_title": "IV (%)",
        },
        width=1250,
        height=850,
    )

    return figura


def crear_heatmap(datos) -> go.Figure:
    """Genera mapa de calor de IV."""

    x, y, z = crear_matrices(datos)

    figura = go.Figure(
        data=[
            go.Heatmap(
                x=x,
                y=y,
                z=z,
                hovertemplate=(
                    "log(K/S): %{x:.4f}<br>"
                    "DTE: %{y:.2f}<br>"
                    "IV: %{z:.2f}%"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.add_vline(
        x=0.0,
        line_dash="dash",
        annotation_text="ATM",
    )

    figura.update_layout(
        title="Volatility Surface - mapa de calor",
        xaxis_title="Log-moneyness ln(K/S)",
        yaxis_title="DTE",
        width=1150,
        height=750,
    )

    return figura


def main() -> None:
    """Genera las visualizaciones de IV."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    configuracion = ConfiguracionVolatilidad()

    datos = generar_superficie_volatilidad(
        configuracion
    )

    datos.to_csv(
        RUTA_RESULTADOS
        / "superficie_volatilidad.csv",
        index=False,
    )

    superficie = crear_superficie(datos)
    heatmap = crear_heatmap(datos)

    superficie.write_html(
        RUTA_RESULTADOS
        / "superficie_volatilidad_3d.html"
    )

    heatmap.write_html(
        RUTA_RESULTADOS
        / "superficie_volatilidad_heatmap.html"
    )

    print("Superficie de volatilidad generada.")
    print(RUTA_RESULTADOS)


if __name__ == "__main__":
    main()