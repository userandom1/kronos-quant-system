from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm


DIAS_ANO = 365.0
MULTIPLICADOR = 100.0


@dataclass(frozen=True, slots=True)
class ContratoRepresentativo:
    """Contrato seleccionado para escenarios."""

    etiqueta: str
    strike: float
    vencimiento: pd.Timestamp
    dte: float
    iv: float
    prima: float
    tipo: str


def precio_black_scholes(
    spot: float | np.ndarray,
    strike: float,
    tiempo: float | np.ndarray,
    volatilidad: float | np.ndarray,
    tipo: str = "CALL",
    tipo_interes: float = 0.04,
    dividendo: float = 0.01,
) -> float | np.ndarray:
    """Calcula precio Black-Scholes europeo."""

    spot_array = np.asarray(
        spot,
        dtype=float,
    )

    tiempo_array = np.maximum(
        np.asarray(
            tiempo,
            dtype=float,
        ),
        1e-8,
    )

    volatilidad_array = np.maximum(
        np.asarray(
            volatilidad,
            dtype=float,
        ),
        1e-6,
    )

    raiz_t = np.sqrt(
        tiempo_array
    )

    d1 = (
        np.log(
            spot_array
            / strike
        )
        + (
            tipo_interes
            - dividendo
            + 0.5
            * volatilidad_array**2
        )
        * tiempo_array
    ) / (
        volatilidad_array
        * raiz_t
    )

    d2 = (
        d1
        - volatilidad_array
        * raiz_t
    )

    descuento_r = np.exp(
        -tipo_interes
        * tiempo_array
    )

    descuento_q = np.exp(
        -dividendo
        * tiempo_array
    )

    if tipo.upper() == "CALL":
        precio = (
            spot_array
            * descuento_q
            * norm.cdf(
                d1
            )
            - strike
            * descuento_r
            * norm.cdf(
                d2
            )
        )

    else:
        precio = (
            strike
            * descuento_r
            * norm.cdf(
                -d2
            )
            - spot_array
            * descuento_q
            * norm.cdf(
                -d1
            )
        )

    return precio


def delta_black_scholes(
    spot: float | np.ndarray,
    strike: float,
    tiempo: float,
    volatilidad: float,
    tipo: str = "CALL",
    tipo_interes: float = 0.04,
    dividendo: float = 0.01,
) -> np.ndarray:
    """Calcula Delta Black-Scholes."""

    spot_array = np.asarray(
        spot,
        dtype=float,
    )

    tiempo = max(
        tiempo,
        1e-8,
    )

    volatilidad = max(
        volatilidad,
        1e-6,
    )

    d1 = (
        np.log(
            spot_array
            / strike
        )
        + (
            tipo_interes
            - dividendo
            + 0.5
            * volatilidad**2
        )
        * tiempo
    ) / (
        volatilidad
        * np.sqrt(
            tiempo
        )
    )

    descuento_q = np.exp(
        -dividendo
        * tiempo
    )

    if tipo.upper() == "CALL":
        return (
            descuento_q
            * norm.cdf(
                d1
            )
        )

    return (
        descuento_q
        * (
            norm.cdf(
                d1
            )
            - 1.0
        )
    )


def seleccionar_vencimiento_objetivo(
    cadena: pd.DataFrame,
    dte_objetivo: int = 35,
) -> pd.Timestamp:
    """Selecciona el vencimiento más cercano al DTE objetivo."""

    datos = cadena.copy()

    datos["vencimiento"] = pd.to_datetime(
        datos["vencimiento"],
        errors="coerce",
    )

    datos["dte"] = pd.to_numeric(
        datos["dte"],
        errors="coerce",
    )

    tabla = (
        datos[
            [
                "vencimiento",
                "dte",
            ]
        ]
        .dropna()
        .drop_duplicates()
    )

    if tabla.empty:
        raise ValueError(
            "No existen vencimientos válidos."
        )

    indice = (
        tabla["dte"]
        .sub(
            dte_objetivo
        )
        .abs()
        .idxmin()
    )

    return pd.Timestamp(
        tabla.loc[
            indice,
            "vencimiento",
        ]
    )


def seleccionar_contratos_representativos(
    cadena: pd.DataFrame,
    spot: float,
    dte_objetivo: int = 35,
    tipo: str = "CALL",
) -> list[ContratoRepresentativo]:
    """Selecciona ITM, ATM y OTM de forma automática."""

    datos = cadena.copy()

    datos["vencimiento"] = pd.to_datetime(
        datos["vencimiento"],
        errors="coerce",
    )

    vencimiento = seleccionar_vencimiento_objetivo(
        datos,
        dte_objetivo=dte_objetivo,
    )

    datos = datos[
        datos[
            "vencimiento"
        ]
        == vencimiento
    ].copy()

    datos = datos[
        datos[
            "tipo_opcion"
        ].astype(
            str
        ).str.upper()
        == tipo.upper()
    ].copy()

    if datos.empty:
        raise ValueError(
            "No existen contratos para "
            f"{tipo} en el vencimiento objetivo."
        )

    datos["strike"] = pd.to_numeric(
        datos["strike"],
        errors="coerce",
    )

    datos["iv"] = pd.to_numeric(
        datos["iv"],
        errors="coerce",
    )

    datos["mid"] = pd.to_numeric(
        datos["mid"],
        errors="coerce",
    )

    datos["dte"] = pd.to_numeric(
        datos["dte"],
        errors="coerce",
    )

    datos = datos.dropna(
        subset=[
            "strike",
            "iv",
            "mid",
            "dte",
        ]
    )

    objetivos = {
        "ITM": spot * 0.97,
        "ATM": spot,
        "OTM": spot * 1.03,
    }

    contratos = []

    for etiqueta, strike_objetivo in objetivos.items():
        indice = (
            datos[
                "strike"
            ]
            .sub(
                strike_objetivo
            )
            .abs()
            .idxmin()
        )

        fila = datos.loc[
            indice
        ]

        contratos.append(
            ContratoRepresentativo(
                etiqueta=etiqueta,
                strike=float(
                    fila["strike"]
                ),
                vencimiento=pd.Timestamp(
                    fila[
                        "vencimiento"
                    ]
                ),
                dte=float(
                    fila["dte"]
                ),
                iv=float(
                    fila["iv"]
                ),
                prima=float(
                    fila["mid"]
                ),
                tipo=tipo.upper(),
            )
        )

    return contratos


def superficie_spot_iv(
    ticker: str,
    spot: float,
    contrato: ContratoRepresentativo,
    ruta_salida: Path,
) -> Path:
    """Genera Spot x IV x P&L."""

    spots = np.linspace(
        spot * 0.90,
        spot * 1.10,
        61,
    )

    desplazamientos_iv = np.linspace(
        -0.10,
        0.10,
        51,
    )

    x, y = np.meshgrid(
        spots,
        desplazamientos_iv,
    )

    volatilidad = np.maximum(
        contrato.iv
        + y,
        0.01,
    )

    tiempo = (
        contrato.dte
        / DIAS_ANO
    )

    precio = precio_black_scholes(
        spot=x,
        strike=contrato.strike,
        tiempo=tiempo,
        volatilidad=volatilidad,
        tipo=contrato.tipo,
    )

    pnl = (
        precio
        - contrato.prima
    ) * MULTIPLICADOR

    figura = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y * 100.0,
                z=pnl,
                colorbar={
                    "title": "P&L $",
                },
            )
        ]
    )

    figura.update_layout(
        title=(
            f"{ticker} {contrato.etiqueta} "
            f"{contrato.tipo} {contrato.strike:g}"
            " — Spot × IV × P&L"
        ),
        scene={
            "xaxis_title": (
                f"{ticker} Spot"
            ),
            "yaxis_title": (
                "Cambio IV (puntos %)"
            ),
            "zaxis_title": (
                "P&L por contrato ($)"
            ),
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 70,
            "b": 0,
        },
    )

    figura.write_html(
        str(
            ruta_salida
        ),
        include_plotlyjs="cdn",
    )

    return ruta_salida


def superficie_spot_tiempo(
    ticker: str,
    spot: float,
    contrato: ContratoRepresentativo,
    ruta_salida: Path,
) -> Path:
    """Genera Spot x tiempo transcurrido x P&L."""

    spots = np.linspace(
        spot * 0.90,
        spot * 1.10,
        61,
    )

    dias_transcurridos = np.linspace(
        0,
        max(
            contrato.dte,
            1,
        ),
        51,
    )

    x, y = np.meshgrid(
        spots,
        dias_transcurridos,
    )

    dias_restantes = np.maximum(
        contrato.dte
        - y,
        0.01,
    )

    tiempo = (
        dias_restantes
        / DIAS_ANO
    )

    precio = precio_black_scholes(
        spot=x,
        strike=contrato.strike,
        tiempo=tiempo,
        volatilidad=contrato.iv,
        tipo=contrato.tipo,
    )

    pnl = (
        precio
        - contrato.prima
    ) * MULTIPLICADOR

    figura = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=pnl,
                colorbar={
                    "title": "P&L $",
                },
            )
        ]
    )

    figura.update_layout(
        title=(
            f"{ticker} {contrato.etiqueta} "
            f"{contrato.tipo} {contrato.strike:g}"
            " — Spot × Tiempo × P&L"
        ),
        scene={
            "xaxis_title": (
                f"{ticker} Spot"
            ),
            "yaxis_title": (
                "Días transcurridos"
            ),
            "zaxis_title": (
                "P&L por contrato ($)"
            ),
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 70,
            "b": 0,
        },
    )

    figura.write_html(
        str(
            ruta_salida
        ),
        include_plotlyjs="cdn",
    )

    return ruta_salida


def grafica_pnl_vencimiento(
    ticker: str,
    spot: float,
    contratos: list[ContratoRepresentativo],
    ruta_salida: Path,
) -> Path:
    """Compara P&L al vencimiento de ITM/ATM/OTM."""

    spots = np.linspace(
        spot * 0.85,
        spot * 1.15,
        250,
    )

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    for contrato in contratos:
        if contrato.tipo == "CALL":
            payoff = np.maximum(
                spots
                - contrato.strike,
                0.0,
            )

        else:
            payoff = np.maximum(
                contrato.strike
                - spots,
                0.0,
            )

        pnl = (
            payoff
            - contrato.prima
        ) * MULTIPLICADOR

        eje.plot(
            spots,
            pnl,
            linewidth=2,
            label=(
                f"{contrato.etiqueta} "
                f"{contrato.strike:g}"
            ),
        )

    eje.axhline(
        0,
        linewidth=1,
    )

    eje.axvline(
        spot,
        linestyle="--",
        linewidth=1.2,
        label=(
            f"Spot {spot:.2f}"
        ),
    )

    eje.set_title(
        f"{ticker} — "
        "P&L al vencimiento"
    )

    eje.set_xlabel(
        f"{ticker} al vencimiento"
    )

    eje.set_ylabel(
        "P&L por contrato ($)"
    )

    eje.grid(
        alpha=0.25
    )

    eje.legend()

    figura.tight_layout()

    figura.savefig(
        ruta_salida,
        dpi=160,
    )

    plt.close(
        figura
    )

    return ruta_salida


def grafica_theta_decay(
    ticker: str,
    spot: float,
    contratos: list[ContratoRepresentativo],
    ruta_salida: Path,
) -> Path:
    """Compara pérdida temporal manteniendo spot e IV constantes."""

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    for contrato in contratos:
        dias = np.linspace(
            0,
            max(
                contrato.dte,
                1,
            ),
            100,
        )

        restantes = np.maximum(
            contrato.dte
            - dias,
            0.01,
        )

        valores = precio_black_scholes(
            spot=spot,
            strike=contrato.strike,
            tiempo=(
                restantes
                / DIAS_ANO
            ),
            volatilidad=contrato.iv,
            tipo=contrato.tipo,
        )

        pnl = (
            valores
            - contrato.prima
        ) * MULTIPLICADOR

        eje.plot(
            dias,
            pnl,
            linewidth=2,
            label=(
                f"{contrato.etiqueta} "
                f"{contrato.strike:g}"
            ),
        )

    eje.axhline(
        0,
        linewidth=1,
    )

    eje.set_title(
        f"{ticker} — "
        "Theta decay comparado"
    )

    eje.set_xlabel(
        "Días transcurridos"
    )

    eje.set_ylabel(
        "P&L teórico ($)"
    )

    eje.grid(
        alpha=0.25
    )

    eje.legend()

    figura.tight_layout()

    figura.savefig(
        ruta_salida,
        dpi=160,
    )

    plt.close(
        figura
    )

    return ruta_salida


def grafica_delta_comparacion(
    ticker: str,
    spot: float,
    contratos: list[ContratoRepresentativo],
    ruta_salida: Path,
) -> Path:
    """Compara Delta de ITM/ATM/OTM frente al spot."""

    spots = np.linspace(
        spot * 0.90,
        spot * 1.10,
        200,
    )

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    for contrato in contratos:
        delta = delta_black_scholes(
            spot=spots,
            strike=contrato.strike,
            tiempo=(
                contrato.dte
                / DIAS_ANO
            ),
            volatilidad=contrato.iv,
            tipo=contrato.tipo,
        )

        eje.plot(
            spots,
            delta,
            linewidth=2,
            label=(
                f"{contrato.etiqueta} "
                f"{contrato.strike:g}"
            ),
        )

    eje.axvline(
        spot,
        linestyle="--",
        linewidth=1.2,
        label=(
            f"Spot {spot:.2f}"
        ),
    )

    eje.set_title(
        f"{ticker} — "
        "Evolución de Delta"
    )

    eje.set_xlabel(
        f"{ticker} Spot"
    )

    eje.set_ylabel(
        "Delta"
    )

    eje.grid(
        alpha=0.25
    )

    eje.legend()

    figura.tight_layout()

    figura.savefig(
        ruta_salida,
        dpi=160,
    )

    plt.close(
        figura
    )

    return ruta_salida


def generar_graficas_escenarios(
    ticker: str,
    cadena: pd.DataFrame,
    spot: float,
    ruta_base: Path,
    dte_objetivo: int = 35,
) -> dict[str, str]:
    """Genera escenarios ITM/ATM/OTM."""

    ruta_base.mkdir(
        parents=True,
        exist_ok=True,
    )

    contratos = seleccionar_contratos_representativos(
        cadena=cadena,
        spot=spot,
        dte_objetivo=dte_objetivo,
        tipo="CALL",
    )

    resultados: dict[
        str,
        str,
    ] = {}

    for contrato in contratos:
        etiqueta = (
            contrato.etiqueta
            .lower()
        )

        ruta_iv = (
            ruta_base
            / (
                "escenario_spot_iv_"
                f"{etiqueta}.html"
            )
        )

        resultados[
            f"escenario_spot_iv_{etiqueta}"
        ] = str(
            superficie_spot_iv(
                ticker=ticker,
                spot=spot,
                contrato=contrato,
                ruta_salida=ruta_iv,
            )
        )

        ruta_tiempo = (
            ruta_base
            / (
                "escenario_spot_tiempo_"
                f"{etiqueta}.html"
            )
        )

        resultados[
            f"escenario_spot_tiempo_{etiqueta}"
        ] = str(
            superficie_spot_tiempo(
                ticker=ticker,
                spot=spot,
                contrato=contrato,
                ruta_salida=ruta_tiempo,
            )
        )

    ruta_pnl = (
        ruta_base
        / "pnl_vencimiento.png"
    )

    resultados[
        "pnl_vencimiento"
    ] = str(
        grafica_pnl_vencimiento(
            ticker=ticker,
            spot=spot,
            contratos=contratos,
            ruta_salida=ruta_pnl,
        )
    )

    ruta_theta = (
        ruta_base
        / "theta_decay.png"
    )

    resultados[
        "theta_decay"
    ] = str(
        grafica_theta_decay(
            ticker=ticker,
            spot=spot,
            contratos=contratos,
            ruta_salida=ruta_theta,
        )
    )

    ruta_delta = (
        ruta_base
        / "delta_comparacion.png"
    )

    resultados[
        "delta_comparacion"
    ] = str(
        grafica_delta_comparacion(
            ticker=ticker,
            spot=spot,
            contratos=contratos,
            ruta_salida=ruta_delta,
        )
    )

    contratos_df = pd.DataFrame(
        [
            {
                "etiqueta": contrato.etiqueta,
                "tipo": contrato.tipo,
                "strike": contrato.strike,
                "vencimiento": (
                    contrato.vencimiento
                ),
                "dte": contrato.dte,
                "iv": contrato.iv,
                "prima_mid": contrato.prima,
                "breakeven": (
                    contrato.strike
                    + contrato.prima
                    if contrato.tipo == "CALL"
                    else contrato.strike
                    - contrato.prima
                ),
            }
            for contrato in contratos
        ]
    )

    contratos_df.to_csv(
        ruta_base
        / "contratos_representativos.csv",
        index=False,
    )

    return resultados