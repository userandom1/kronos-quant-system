from math import exp
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    theta_por_dia,
    vanna_por_punto,
    vega_por_punto,
)

from motor_opciones.superficie_volatilidad import (
    ConfiguracionVolatilidad,
    volatilidad_implicita,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "greeks_iv_surface"
)


FUNCIONES = {
    "delta": delta,
    "gamma": gamma,
    "theta": theta_por_dia,
    "vega": vega_por_punto,
    "vanna": vanna_por_punto,
    "delta_decay": delta_decay_por_dia,
}


DTE = (
    0.25,
    0.50,
    1.0,
    2.0,
    3.0,
    5.0,
    7.0,
    10.0,
    14.0,
    21.0,
    30.0,
    45.0,
    60.0,
    90.0,
    120.0,
    180.0,
    270.0,
    365.0,
)


def generar_superficie_griega(
    nombre: str,
    tipo: str,
    spot: float = 100.0,
) -> pd.DataFrame:
    """Genera una Greek utilizando una IV distinta en cada punto."""

    configuracion_iv = ConfiguracionVolatilidad()

    log_moneyness = np.linspace(
        np.log(0.70),
        np.log(1.30),
        181,
    )

    funcion = FUNCIONES[nombre]

    filas = []

    for dte in DTE:
        for log_m in log_moneyness:
            ratio = exp(float(log_m))

            strike = (
                spot
                * ratio
            )

            iv = volatilidad_implicita(
                float(log_m),
                float(dte),
                configuracion_iv,
            )

            parametros = ParametrosOpcion(
                spot=spot,
                strike=strike,
                tiempo=dte / 365.0,
                volatilidad=iv,
                tipo_interes=0.04,
                dividendo=0.01,
                tipo=tipo,
            )

            valor = float(
                funcion(parametros)
            )

            filas.append(
                {
                    "tipo": tipo,
                    "griega": nombre,
                    "dte": dte,
                    "log_moneyness": float(log_m),
                    "moneyness": ratio,
                    "strike": strike,
                    "iv": iv,
                    "iv_pct": iv * 100.0,
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )


def crear_3d(
    nombre: str,
    tipo: str,
    datos: pd.DataFrame,
) -> go.Figure:
    """Construye una superficie 3D."""

    pivot = datos.pivot(
        index="dte",
        columns="log_moneyness",
        values="valor",
    )

    x = pivot.columns.to_numpy()
    y = pivot.index.to_numpy()
    z = pivot.to_numpy()

    figura = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                hovertemplate=(
                    "log(K/S): %{x:.4f}<br>"
                    "DTE: %{y:.2f}<br>"
                    "Greek: %{z:.8f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figura.update_layout(
        title=(
            f"{nombre.upper()} - {tipo.upper()} "
            "- IV Surface"
        ),
        scene={
            "xaxis_title": "log(K/S)",
            "yaxis_title": "DTE",
            "zaxis_title": nombre,
        },
        width=1250,
        height=850,
    )

    return figura


def main() -> None:
    """Genera todas las superficies con volatilidad variable."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    for tipo in (
        "call",
        "put",
    ):
        for nombre in FUNCIONES:
            print(
                f"Calculando {nombre} {tipo}..."
            )

            datos = generar_superficie_griega(
                nombre,
                tipo,
            )

            carpeta = (
                RUTA_RESULTADOS
                / nombre
                / tipo
            )

            carpeta.mkdir(
                parents=True,
                exist_ok=True,
            )

            datos.to_csv(
                carpeta
                / "datos.csv",
                index=False,
            )

            figura = crear_3d(
                nombre,
                tipo,
                datos,
            )

            figura.write_html(
                carpeta
                / "superficie_3d.html"
            )

    print()
    print("Superficies con IV variable completadas.")
    print(RUTA_RESULTADOS)


if __name__ == "__main__":
    main()