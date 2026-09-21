from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    theta_por_dia,
    vanna_por_punto,
    vega_por_punto,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "options_chain_real"
    / "QQQ"
)


TICKER = "QQQ"

MAX_VENCIMIENTOS = 12


def obtener_spot(
    ticker: yf.Ticker,
) -> float:
    """Obtiene el precio spot actual."""

    historico = ticker.history(
        period="5d",
        interval="1d",
    )

    if historico.empty:
        raise RuntimeError(
            "No se ha podido obtener el spot."
        )

    return float(
        historico[
            "Close"
        ].iloc[-1]
    )


def calcular_dte(
    vencimiento: str,
) -> float:
    """Calcula DTE aproximado."""

    fecha_vencimiento = datetime.strptime(
        vencimiento,
        "%Y-%m-%d",
    ).replace(
        tzinfo=timezone.utc
    )

    ahora = datetime.now(
        timezone.utc
    )

    segundos = (
        fecha_vencimiento
        - ahora
    ).total_seconds()

    dias = (
        segundos
        / 86400.0
    )

    return max(
        dias,
        0.25,
    )


def preparar_lado(
    datos: pd.DataFrame,
    tipo: str,
    vencimiento: str,
    spot: float,
) -> pd.DataFrame:
    """Normaliza calls o puts y calcula las Greeks."""

    salida = datos.copy()

    salida["tipo"] = tipo

    salida["vencimiento"] = (
        vencimiento
    )

    salida["dte"] = calcular_dte(
        vencimiento
    )

    salida["spot"] = spot

    salida["moneyness"] = (
        salida["strike"]
        / spot
    )

    salida["log_moneyness"] = np.log(
        salida["moneyness"]
    )

    salida["mid"] = (
        salida["bid"]
        + salida["ask"]
    ) / 2.0

    resultados = []

    for fila in salida.itertuples():
        iv = float(
            fila.impliedVolatility
        )

        if (
            not np.isfinite(iv)
            or iv <= 0
        ):
            resultados.append(
                (
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan,
                )
            )

            continue

        parametros = ParametrosOpcion(
            spot=spot,
            strike=float(
                fila.strike
            ),
            tiempo=max(
                float(fila.dte)
                / 365.0,
                1e-6,
            ),
            volatilidad=iv,
            tipo_interes=0.04,
            dividendo=0.01,
            tipo=tipo,
        )

        resultados.append(
            (
                delta(parametros),
                gamma(parametros),
                theta_por_dia(
                    parametros
                ),
                vega_por_punto(
                    parametros
                ),
                vanna_por_punto(
                    parametros
                ),
                delta_decay_por_dia(
                    parametros
                ),
            )
        )

    (
        salida["delta"],
        salida["gamma"],
        salida["theta"],
        salida["vega"],
        salida["vanna"],
        salida["delta_decay"],
    ) = zip(
        *resultados
    )

    return salida


def main() -> None:
    """Descarga una options chain real de QQQ."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ticker = yf.Ticker(
        TICKER
    )

    spot = obtener_spot(
        ticker
    )

    vencimientos = list(
        ticker.options
    )

    if not vencimientos:
        raise RuntimeError(
            "Yahoo Finance no devolvió vencimientos."
        )

    vencimientos = vencimientos[
        :MAX_VENCIMIENTOS
    ]

    print(
        f"QQQ spot: {spot:.2f}"
    )

    print(
        f"Vencimientos: {len(vencimientos)}"
    )

    bloques = []

    for numero, vencimiento in enumerate(
        vencimientos,
        start=1,
    ):
        print(
            f"[{numero}/{len(vencimientos)}] "
            f"{vencimiento}"
        )

        cadena = ticker.option_chain(
            vencimiento
        )

        calls = preparar_lado(
            cadena.calls,
            "call",
            vencimiento,
            spot,
        )

        puts = preparar_lado(
            cadena.puts,
            "put",
            vencimiento,
            spot,
        )

        bloques.extend(
            [
                calls,
                puts,
            ]
        )

    resultado = pd.concat(
        bloques,
        ignore_index=True,
    )

    columnas = [
        "contractSymbol",
        "tipo",
        "vencimiento",
        "dte",
        "spot",
        "strike",
        "moneyness",
        "log_moneyness",
        "lastPrice",
        "bid",
        "ask",
        "mid",
        "volume",
        "openInterest",
        "impliedVolatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "delta_decay",
    ]

    columnas = [
        columna
        for columna in columnas
        if columna in resultado.columns
    ]

    resultado = resultado[
        columnas
    ]

    ruta = (
        RUTA_RESULTADOS
        / "cadena_qqq_griegas.csv"
    )

    resultado.to_csv(
        ruta,
        index=False,
    )

    print()
    print(
        f"Contratos: {len(resultado)}"
    )

    print(
        f"Archivo: {ruta}"
    )


if __name__ == "__main__":
    main()