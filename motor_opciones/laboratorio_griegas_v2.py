from pathlib import Path
import webbrowser

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from motor_opciones.superficies_v2 import (
    ConfiguracionMercado,
    NOMBRES_GRIEGAS,
    PERFILES_GRIEGAS,
    calcular_atm_por_dte_e_iv,
    calcular_comparacion_iv,
    calcular_cortes_dte,
    calcular_superficie,
)


# =============================================================================
# RUTAS
# =============================================================================

RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "laboratorio_griegas_v2"
)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

GRIEGAS = (
    "delta",
    "gamma",
    "theta",
    "vega",
    "vanna",
    "delta_decay",
)

TIPOS_OPCION = (
    "call",
    "put",
)

ABRIR_INDICE_AL_FINAL = True


# =============================================================================
# UTILIDADES
# =============================================================================


def obtener_matriz(
    datos: pd.DataFrame,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Convierte una superficie tabular a matrices X, Y y Z."""

    pivot = datos.pivot(
        index="dte",
        columns="log_moneyness",
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

    return x, y, z


def titulo_tipo(
    tipo_opcion: str,
) -> str:
    """Devuelve el nombre legible del tipo de opción."""

    if tipo_opcion == "call":
        return "Call"

    return "Put"


# =============================================================================
# SUPERFICIE 3D
# =============================================================================


def crear_superficie_3d(
    nombre_griega: str,
    tipo_opcion: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea una superficie 3D interactiva."""

    x, y, z = obtener_matriz(
        datos
    )

    figura = go.Figure()

    figura.add_trace(
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
                "DTE: %{y:.2f} días<br>"
                "Valor: %{z:.8f}"
                "<extra></extra>"
            ),
        )
    )

    figura.update_layout(
        title=(
            f"{NOMBRES_GRIEGAS[nombre_griega]} "
            f"- {titulo_tipo(tipo_opcion)} "
            "- Superficie 3D"
        ),
        scene={
            "xaxis_title": (
                "Log-moneyness ln(K/S)"
            ),
            "yaxis_title": (
                "DTE"
            ),
            "zaxis_title": (
                NOMBRES_GRIEGAS[
                    nombre_griega
                ]
            ),
        },
        width=1250,
        height=850,
        margin={
            "l": 20,
            "r": 20,
            "t": 80,
            "b": 20,
        },
    )

    return figura


# =============================================================================
# HEATMAP
# =============================================================================


def crear_mapa_calor(
    nombre_griega: str,
    tipo_opcion: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea un mapa de calor de la superficie."""

    x, y, z = obtener_matriz(
        datos
    )

    figura = go.Figure()

    figura.add_trace(
        go.Heatmap(
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
                "DTE: %{y:.2f} días<br>"
                "Valor: %{z:.8f}"
                "<extra></extra>"
            ),
        )
    )

    figura.add_vline(
        x=0.0,
        line_dash="dash",
        annotation_text="ATM",
    )

    figura.update_layout(
        title=(
            f"{NOMBRES_GRIEGAS[nombre_griega]} "
            f"- {titulo_tipo(tipo_opcion)} "
            "- Mapa de calor"
        ),
        xaxis_title=(
            "Log-moneyness ln(K/S)"
        ),
        yaxis_title="DTE",
        width=1150,
        height=750,
    )

    return figura


# =============================================================================
# CORTES POR DTE
# =============================================================================


def crear_cortes_dte(
    nombre_griega: str,
    tipo_opcion: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Representa Greek vs log-moneyness para varios vencimientos."""

    figura = go.Figure()

    for dte in sorted(
        datos["dte"].unique()
    ):
        muestra = datos[
            datos["dte"]
            == dte
        ]

        figura.add_trace(
            go.Scatter(
                x=muestra[
                    "log_moneyness"
                ],
                y=muestra["valor"],
                mode="lines",
                name=(
                    f"{dte:g} DTE"
                ),
                customdata=muestra[
                    "moneyness"
                ],
                hovertemplate=(
                    "log(K/S): %{x:.4f}<br>"
                    "K/S: %{customdata:.4f}<br>"
                    "Valor: %{y:.8f}"
                    "<extra></extra>"
                ),
            )
        )

    figura.add_vline(
        x=0.0,
        line_dash="dash",
        annotation_text="ATM",
    )

    figura.update_layout(
        title=(
            f"{NOMBRES_GRIEGAS[nombre_griega]} "
            f"- {titulo_tipo(tipo_opcion)} "
            "- Cortes por DTE"
        ),
        xaxis_title=(
            "Log-moneyness ln(K/S)"
        ),
        yaxis_title=(
            NOMBRES_GRIEGAS[
                nombre_griega
            ]
        ),
        width=1200,
        height=700,
    )

    return figura


# =============================================================================
# ATM VS DTE SEGÚN IV
# =============================================================================


def crear_atm_dte_iv(
    nombre_griega: str,
    tipo_opcion: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Representa la Greek ATM a través del tiempo para distintos IV."""

    figura = go.Figure()

    for volatilidad in sorted(
        datos[
            "volatilidad"
        ].unique()
    ):
        muestra = datos[
            datos["volatilidad"]
            == volatilidad
        ]

        figura.add_trace(
            go.Scatter(
                x=muestra["dte"],
                y=muestra["valor"],
                mode="lines+markers",
                name=(
                    f"IV {volatilidad * 100:.0f}%"
                ),
                hovertemplate=(
                    "DTE: %{x:.2f}<br>"
                    "Valor: %{y:.8f}"
                    "<extra></extra>"
                ),
            )
        )

    figura.update_layout(
        title=(
            f"{NOMBRES_GRIEGAS[nombre_griega]} ATM "
            f"- {titulo_tipo(tipo_opcion)} "
            "- DTE vs IV"
        ),
        xaxis_title="DTE",
        yaxis_title=(
            NOMBRES_GRIEGAS[
                nombre_griega
            ]
        ),
        width=1200,
        height=700,
    )

    return figura


# =============================================================================
# COMPARACIÓN ENTRE REGÍMENES DE IV
# =============================================================================


def crear_comparacion_iv(
    nombre_griega: str,
    tipo_opcion: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Compara la forma de la Greek para diferentes niveles de IV."""

    figura = go.Figure()

    dte = float(
        datos["dte"].iloc[0]
    )

    for volatilidad in sorted(
        datos[
            "volatilidad"
        ].unique()
    ):
        muestra = datos[
            datos["volatilidad"]
            == volatilidad
        ]

        figura.add_trace(
            go.Scatter(
                x=muestra[
                    "log_moneyness"
                ],
                y=muestra["valor"],
                mode="lines",
                name=(
                    f"IV {volatilidad * 100:.0f}%"
                ),
                customdata=muestra[
                    "moneyness"
                ],
                hovertemplate=(
                    "log(K/S): %{x:.4f}<br>"
                    "K/S: %{customdata:.4f}<br>"
                    "Valor: %{y:.8f}"
                    "<extra></extra>"
                ),
            )
        )

    figura.add_vline(
        x=0.0,
        line_dash="dash",
        annotation_text="ATM",
    )

    figura.update_layout(
        title=(
            f"{NOMBRES_GRIEGAS[nombre_griega]} "
            f"- {titulo_tipo(tipo_opcion)} "
            f"- Comparación IV a {dte:g} DTE"
        ),
        xaxis_title=(
            "Log-moneyness ln(K/S)"
        ),
        yaxis_title=(
            NOMBRES_GRIEGAS[
                nombre_griega
            ]
        ),
        width=1200,
        height=700,
    )

    return figura


# =============================================================================
# GUARDADO
# =============================================================================


def guardar_html(
    figura: go.Figure,
    ruta: Path,
) -> None:
    """Guarda una figura Plotly autónoma."""

    figura.write_html(
        ruta,
        include_plotlyjs=True,
        full_html=True,
    )


# =============================================================================
# ÍNDICE
# =============================================================================


def crear_indice(
    enlaces: list[
        tuple[str, Path]
    ],
) -> Path:
    """Genera una página de entrada al laboratorio."""

    ruta_indice = (
        RUTA_RESULTADOS
        / "indice.html"
    )

    lineas = [
        "<!DOCTYPE html>",
        "<html lang='es'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>Laboratorio de Griegas V2</title>",
        "<style>",
        "body {",
        "font-family: Arial, sans-serif;",
        "max-width: 1100px;",
        "margin: 40px auto;",
        "padding: 0 20px;",
        "}",
        "h1 { margin-bottom: 30px; }",
        "li { margin: 8px 0; }",
        "a { text-decoration: none; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Laboratorio de Griegas V2</h1>",
        "<p>",
        "Superficies y estudios Black-Scholes-Merton.",
        "</p>",
        "<ul>",
    ]

    for titulo, ruta in enlaces:
        relativa = ruta.relative_to(
            RUTA_RESULTADOS
        )

        lineas.append(
            (
                "<li>"
                f"<a href='{relativa.as_posix()}'>"
                f"{titulo}"
                "</a>"
                "</li>"
            )
        )

    lineas.extend(
        [
            "</ul>",
            "</body>",
            "</html>",
        ]
    )

    ruta_indice.write_text(
        "\n".join(
            lineas
        ),
        encoding="utf-8",
    )

    return ruta_indice


# =============================================================================
# EJECUCIÓN
# =============================================================================


def main() -> None:
    """Genera el laboratorio completo V2."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    mercado = ConfiguracionMercado()

    enlaces: list[
        tuple[str, Path]
    ] = []

    print()
    print("=" * 80)
    print("LABORATORIO DE GRIEGAS V2")
    print("=" * 80)

    print(
        f"Spot: {mercado.spot:.2f}"
    )

    print(
        "IV base:"
        f" {mercado.volatilidad_base * 100:.0f}%"
    )

    print()

    for nombre_griega in GRIEGAS:
        perfil = PERFILES_GRIEGAS[
            nombre_griega
        ]

        for tipo_opcion in TIPOS_OPCION:
            print(
                f"Generando "
                f"{nombre_griega} "
                f"{tipo_opcion}..."
            )

            carpeta = (
                RUTA_RESULTADOS
                / nombre_griega
                / tipo_opcion
            )

            carpeta.mkdir(
                parents=True,
                exist_ok=True,
            )

            # -------------------------------------------------------------
            # Superficie base
            # -------------------------------------------------------------

            superficie = calcular_superficie(
                nombre_griega,
                tipo_opcion,
                mercado,
            )

            ruta_csv = (
                carpeta
                / "superficie_base.csv"
            )

            superficie.to_csv(
                ruta_csv,
                index=False,
            )

            figura_3d = crear_superficie_3d(
                nombre_griega,
                tipo_opcion,
                superficie,
            )

            ruta_3d = (
                carpeta
                / "superficie_3d.html"
            )

            guardar_html(
                figura_3d,
                ruta_3d,
            )

            enlaces.append(
                (
                    (
                        f"{NOMBRES_GRIEGAS[nombre_griega]} "
                        f"{titulo_tipo(tipo_opcion)} "
                        "- Superficie 3D"
                    ),
                    ruta_3d,
                )
            )

            # -------------------------------------------------------------
            # Heatmap
            # -------------------------------------------------------------

            mapa = crear_mapa_calor(
                nombre_griega,
                tipo_opcion,
                superficie,
            )

            ruta_mapa = (
                carpeta
                / "mapa_calor.html"
            )

            guardar_html(
                mapa,
                ruta_mapa,
            )

            enlaces.append(
                (
                    (
                        f"{NOMBRES_GRIEGAS[nombre_griega]} "
                        f"{titulo_tipo(tipo_opcion)} "
                        "- Mapa de calor"
                    ),
                    ruta_mapa,
                )
            )

            # -------------------------------------------------------------
            # Cortes DTE
            # -------------------------------------------------------------

            cortes = calcular_cortes_dte(
                nombre_griega,
                tipo_opcion,
                mercado,
            )

            cortes.to_csv(
                carpeta
                / "cortes_dte.csv",
                index=False,
            )

            figura_cortes = (
                crear_cortes_dte(
                    nombre_griega,
                    tipo_opcion,
                    cortes,
                )
            )

            ruta_cortes = (
                carpeta
                / "cortes_dte.html"
            )

            guardar_html(
                figura_cortes,
                ruta_cortes,
            )

            enlaces.append(
                (
                    (
                        f"{NOMBRES_GRIEGAS[nombre_griega]} "
                        f"{titulo_tipo(tipo_opcion)} "
                        "- Cortes por DTE"
                    ),
                    ruta_cortes,
                )
            )

            # -------------------------------------------------------------
            # ATM por DTE e IV
            # -------------------------------------------------------------

            atm = calcular_atm_por_dte_e_iv(
                nombre_griega,
                tipo_opcion,
                mercado,
            )

            atm.to_csv(
                carpeta
                / "atm_dte_iv.csv",
                index=False,
            )

            figura_atm = crear_atm_dte_iv(
                nombre_griega,
                tipo_opcion,
                atm,
            )

            ruta_atm = (
                carpeta
                / "atm_dte_iv.html"
            )

            guardar_html(
                figura_atm,
                ruta_atm,
            )

            enlaces.append(
                (
                    (
                        f"{NOMBRES_GRIEGAS[nombre_griega]} "
                        f"{titulo_tipo(tipo_opcion)} "
                        "- ATM por DTE e IV"
                    ),
                    ruta_atm,
                )
            )

            # -------------------------------------------------------------
            # Comparación IV
            # -------------------------------------------------------------

            comparacion_iv = (
                calcular_comparacion_iv(
                    nombre_griega,
                    tipo_opcion,
                    mercado,
                )
            )

            comparacion_iv.to_csv(
                carpeta
                / "comparacion_iv.csv",
                index=False,
            )

            figura_iv = (
                crear_comparacion_iv(
                    nombre_griega,
                    tipo_opcion,
                    comparacion_iv,
                )
            )

            ruta_iv = (
                carpeta
                / "comparacion_iv.html"
            )

            guardar_html(
                figura_iv,
                ruta_iv,
            )

            enlaces.append(
                (
                    (
                        f"{NOMBRES_GRIEGAS[nombre_griega]} "
                        f"{titulo_tipo(tipo_opcion)} "
                        "- Comparación IV"
                    ),
                    ruta_iv,
                )
            )

    ruta_indice = crear_indice(
        enlaces
    )

    print()
    print("=" * 80)
    print("GENERACIÓN COMPLETADA")
    print("=" * 80)

    print(
        f"Índice principal: {ruta_indice}"
    )

    if ABRIR_INDICE_AL_FINAL:
        webbrowser.open(
            ruta_indice.as_uri()
        )


if __name__ == "__main__":
    main()