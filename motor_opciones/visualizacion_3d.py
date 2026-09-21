from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from motor_opciones.superficies import (
    ConfiguracionSuperficie,
    calcular_todas_las_superficies,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "greeks_3d"
)


TITULOS = {
    "delta": "Delta",
    "gamma": "Gamma",
    "theta": "Theta diario",
    "vega": "Vega por punto de IV",
    "vanna": "Vanna por punto de IV",
    "delta_decay": "Delta Decay diario",
}


def convertir_a_matriz(
    datos: pd.DataFrame,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Convierte la superficie tabular a matrices X, Y y Z."""

    pivot = datos.pivot(
        index="dte",
        columns="moneyness",
        values="valor",
    )

    x = pivot.columns.to_numpy(
        dtype=float
    )

    y = pivot.index.to_numpy(
        dtype=float
    )

    z = pivot.to_numpy(
        dtype=float
    )

    return (
        x,
        y,
        z,
    )


def crear_superficie_3d(
    nombre_griega: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea una superficie 3D interactiva."""

    x, y, z = convertir_a_matriz(
        datos
    )

    figura = go.Figure()

    figura.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            hovertemplate=(
                "Moneyness: %{x:.3f}<br>"
                "DTE: %{y:.1f} días<br>"
                "Valor: %{z:.6f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_trace(
        go.Scatter3d(
            x=np.ones_like(
                y
            ),
            y=y,
            z=np.zeros_like(
                y
            ),
            mode="lines",
            name="ATM",
            line={
                "width": 4,
            },
        )
    )

    figura.update_layout(
        title=(
            f"{TITULOS[nombre_griega]} "
            "- Superficie 3D"
        ),
        scene={
            "xaxis_title": (
                "Moneyness K/S"
            ),
            "yaxis_title": (
                "DTE"
            ),
            "zaxis_title": (
                TITULOS[
                    nombre_griega
                ]
            ),
        },
        width=1200,
        height=800,
        margin={
            "l": 20,
            "r": 20,
            "t": 70,
            "b": 20,
        },
    )

    return figura


def crear_heatmap(
    nombre_griega: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea un heatmap 2D de una Greek."""

    x, y, z = convertir_a_matriz(
        datos
    )

    figura = go.Figure()

    figura.add_trace(
        go.Heatmap(
            x=x,
            y=y,
            z=z,
            hovertemplate=(
                "Moneyness: %{x:.3f}<br>"
                "DTE: %{y:.1f} días<br>"
                "Valor: %{z:.6f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_vline(
        x=1.0,
        line_dash="dash",
        annotation_text="ATM",
    )

    figura.update_layout(
        title=(
            f"{TITULOS[nombre_griega]} "
            "- Heatmap"
        ),
        xaxis_title=(
            "Moneyness K/S"
        ),
        yaxis_title=(
            "DTE"
        ),
        width=1100,
        height=700,
    )

    return figura


def guardar_figura(
    figura: go.Figure,
    nombre_archivo: str,
) -> None:
    """Guarda una figura Plotly como HTML interactivo."""

    ruta = (
        RUTA_RESULTADOS
        / nombre_archivo
    )

    figura.write_html(
        ruta,
        include_plotlyjs=True,
        full_html=True,
    )


def main() -> None:
    """Genera todas las superficies y heatmaps."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    configuracion = ConfiguracionSuperficie(
        spot=100.0,
        volatilidad=0.20,
        tipo_interes=0.04,
        dividendo=0.01,
        tipo="call",
        moneyness_min=0.80,
        moneyness_max=1.20,
        puntos_moneyness=81,
        dte_min=1,
        dte_max=365,
        puntos_dte=90,
    )

    print(
        "Calculando superficies..."
    )

    superficies = (
        calcular_todas_las_superficies(
            configuracion
        )
    )

    for nombre_griega, datos in superficies.items():
        print(
            f"Generando {nombre_griega}..."
        )

        datos.to_csv(
            RUTA_RESULTADOS
            / f"{nombre_griega}.csv",
            index=False,
        )

        figura_3d = (
            crear_superficie_3d(
                nombre_griega,
                datos,
            )
        )

        heatmap = (
            crear_heatmap(
                nombre_griega,
                datos,
            )
        )

        guardar_figura(
            figura_3d,
            (
                f"{nombre_griega}"
                "_superficie_3d.html"
            ),
        )

        guardar_figura(
            heatmap,
            (
                f"{nombre_griega}"
                "_heatmap.html"
            ),
        )

    print()
    print(
        "Generación completada."
    )

    print(
        "Resultados:"
    )

    print(
        RUTA_RESULTADOS
    )


if __name__ == "__main__":
    main()