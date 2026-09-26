from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go


MAPEO_COLUMNAS = {
    "tipo_opcion": "tipo",
    "theta_dia": "theta",
    "vega_1pt": "vega",
    "vanna_1pt": "vanna",
    "charm_dia": "charm",
}


def asegurar_directorio(
    ruta: Path,
) -> None:
    """Crea un directorio si no existe."""

    ruta.mkdir(
        parents=True,
        exist_ok=True,
    )


def normalizar_cadena(
    cadena: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza la cadena V2 para visualización."""

    datos = cadena.copy()

    datos = datos.rename(
        columns={
            origen: destino
            for origen, destino
            in MAPEO_COLUMNAS.items()
            if origen in datos.columns
        }
    )

    if "tipo" in datos.columns:
        datos["tipo"] = (
            datos["tipo"]
            .astype(str)
            .str.upper()
        )

    if "vencimiento" in datos.columns:
        datos["vencimiento"] = pd.to_datetime(
            datos["vencimiento"],
            errors="coerce",
        )

    if "dte" not in datos.columns:
        if "vencimiento" in datos.columns:
            hoy = pd.Timestamp.now().normalize()

            datos["dte"] = (
                datos["vencimiento"]
                - hoy
            ).dt.days

    columnas_numericas = [
        "strike",
        "dte",
        "iv",
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "charm",
        "open_interest",
        "volumen",
        "gex_1pct",
        "dex",
        "vanna_exposure_1pt",
        "charm_exposure_dia",
    ]

    for columna in columnas_numericas:
        if columna in datos.columns:
            datos[columna] = pd.to_numeric(
                datos[columna],
                errors="coerce",
            )

    return datos


def filtrar_rango_strikes(
    datos: pd.DataFrame,
    spot: float,
    rango_pct: float = 0.20,
) -> pd.DataFrame:
    """Limita strikes alrededor del spot."""

    minimo = spot * (
        1.0 - rango_pct
    )

    maximo = spot * (
        1.0 + rango_pct
    )

    return datos[
        datos["strike"].between(
            minimo,
            maximo,
        )
    ].copy()


def graficar_greek_2d(
    cadena: pd.DataFrame,
    ticker: str,
    greek: str,
    spot: float,
    ruta_salida: Path,
) -> Path:
    """Genera un Greek 2D para el vencimiento más cercano."""

    datos = normalizar_cadena(
        cadena
    )

    datos = filtrar_rango_strikes(
        datos,
        spot,
    )

    if greek not in datos.columns:
        raise ValueError(
            f"No existe {greek}."
        )

    if "dte" in datos.columns:
        dte_validos = (
            datos["dte"]
            .dropna()
            .unique()
        )

        if len(dte_validos):
            dte_minimo = min(
                dte_validos
            )

            datos = datos[
                datos["dte"]
                == dte_minimo
            ]

    asegurar_directorio(
        ruta_salida.parent
    )

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    for tipo in [
        "CALL",
        "PUT",
    ]:
        subset = (
            datos[
                datos["tipo"]
                == tipo
            ]
            .sort_values(
                "strike"
            )
        )

        if subset.empty:
            continue

        eje.plot(
            subset["strike"],
            subset[greek],
            label=tipo,
            linewidth=2,
        )

    eje.axvline(
        spot,
        linestyle="--",
        linewidth=1.2,
        label=f"Spot {spot:.2f}",
    )

    eje.set_title(
        f"{ticker} — "
        f"{greek.upper()} por strike"
    )

    eje.set_xlabel(
        "Strike"
    )

    eje.set_ylabel(
        greek.upper()
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


def construir_superficie(
    cadena: pd.DataFrame,
    valor: str,
    tipo: str,
    spot: float,
) -> pd.DataFrame:
    """Construye superficie DTE × strike."""

    datos = normalizar_cadena(
        cadena
    )

    datos = filtrar_rango_strikes(
        datos,
        spot,
    )

    tipo = tipo.upper()

    datos = datos[
        datos["tipo"]
        == tipo
    ].copy()

    necesarios = {
        "strike",
        "dte",
        valor,
    }

    faltantes = (
        necesarios
        - set(
            datos.columns
        )
    )

    if faltantes:
        raise ValueError(
            f"Faltan columnas: "
            f"{sorted(faltantes)}"
        )

    datos = datos.dropna(
        subset=[
            "strike",
            "dte",
            valor,
        ]
    )

    superficie = datos.pivot_table(
        index="dte",
        columns="strike",
        values=valor,
        aggfunc="mean",
    )

    superficie = (
        superficie
        .sort_index()
        .sort_index(
            axis=1
        )
    )

    if superficie.empty:
        raise ValueError(
            f"Superficie vacía: "
            f"{valor} {tipo}"
        )

    return superficie


def graficar_superficie_3d(
    cadena: pd.DataFrame,
    ticker: str,
    valor: str,
    tipo: str,
    spot: float,
    ruta_salida: Path,
) -> Path:
    """Genera superficie 3D interactiva."""

    superficie = construir_superficie(
        cadena=cadena,
        valor=valor,
        tipo=tipo,
        spot=spot,
    )

    asegurar_directorio(
        ruta_salida.parent
    )

    x = np.asarray(
        superficie.columns,
        dtype=float,
    )

    y = np.asarray(
        superficie.index,
        dtype=float,
    )

    z = superficie.to_numpy(
        dtype=float
    )

    figura = go.Figure()

    figura.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            connectgaps=True,
            name=valor.upper(),
        )
    )

    figura.update_layout(
        title=(
            f"{ticker} — "
            f"{valor.upper()} Surface "
            f"({tipo.upper()})"
        ),
        scene={
            "xaxis_title": "Strike",
            "yaxis_title": "DTE",
            "zaxis_title": valor.upper(),
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 60,
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


def graficar_exposicion_strike(
    cadena: pd.DataFrame,
    ticker: str,
    columna: str,
    spot: float,
    ruta_salida: Path,
) -> Path:
    """Grafica exposición agregada por strike."""

    datos = normalizar_cadena(
        cadena
    )

    datos = filtrar_rango_strikes(
        datos,
        spot,
    )

    if columna not in datos.columns:
        raise ValueError(
            f"No existe {columna}."
        )

    agregado = (
        datos
        .groupby(
            "strike",
            as_index=False,
        )[
            columna
        ]
        .sum()
        .sort_values(
            "strike"
        )
    )

    asegurar_directorio(
        ruta_salida.parent
    )

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    eje.bar(
        agregado["strike"],
        agregado[columna],
        width=1.0,
    )

    eje.axvline(
        spot,
        linestyle="--",
        linewidth=1.2,
        label=f"Spot {spot:.2f}",
    )

    eje.axhline(
        0,
        linewidth=1,
    )

    eje.set_title(
        f"{ticker} — "
        f"{columna} por strike"
    )

    eje.set_xlabel(
        "Strike"
    )

    eje.set_ylabel(
        columna
    )

    eje.legend()

    eje.grid(
        alpha=0.20
    )

    figura.tight_layout()

    figura.savefig(
        ruta_salida,
        dpi=160,
    )

    plt.close(
        figura
    )

    return ruta_salida


def graficar_oi_strike(
    cadena: pd.DataFrame,
    ticker: str,
    spot: float,
    ruta_salida: Path,
) -> Path:
    """Grafica Open Interest CALL y PUT."""

    datos = normalizar_cadena(
        cadena
    )

    datos = filtrar_rango_strikes(
        datos,
        spot,
    )

    if "open_interest" not in datos.columns:
        raise ValueError(
            "No existe open_interest."
        )

    agregado = (
        datos
        .groupby(
            [
                "strike",
                "tipo",
            ],
            as_index=False,
        )[
            "open_interest"
        ]
        .sum()
    )

    pivot = agregado.pivot_table(
        index="strike",
        columns="tipo",
        values="open_interest",
        fill_value=0,
    )

    asegurar_directorio(
        ruta_salida.parent
    )

    figura, eje = plt.subplots(
        figsize=(
            13,
            7,
        )
    )

    if "CALL" in pivot.columns:
        eje.plot(
            pivot.index,
            pivot["CALL"],
            label="CALL OI",
            linewidth=2,
        )

    if "PUT" in pivot.columns:
        eje.plot(
            pivot.index,
            pivot["PUT"],
            label="PUT OI",
            linewidth=2,
        )

    eje.axvline(
        spot,
        linestyle="--",
        linewidth=1.2,
        label=f"Spot {spot:.2f}",
    )

    eje.set_title(
        f"{ticker} — "
        "Open Interest por strike"
    )

    eje.set_xlabel(
        "Strike"
    )

    eje.set_ylabel(
        "Open Interest"
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


def generar_pack_graficas(
    ticker: str,
    cadena: pd.DataFrame,
    spot: float,
    ruta_base: Path,
) -> dict[str, str]:
    """Genera todas las visualizaciones disponibles."""

    asegurar_directorio(
        ruta_base
    )

    datos = normalizar_cadena(
        cadena
    )

    resultados: dict[
        str,
        str,
    ] = {}

    for greek in [
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "charm",
    ]:
        if greek not in datos.columns:
            continue

        ruta = (
            ruta_base
            / f"{greek}_2d.png"
        )

        resultados[
            f"{greek}_2d"
        ] = str(
            graficar_greek_2d(
                cadena=datos,
                ticker=ticker,
                greek=greek,
                spot=spot,
                ruta_salida=ruta,
            )
        )

    exposiciones = [
        "gex_1pct",
        "dex",
        "vanna_exposure_1pt",
        "charm_exposure_dia",
    ]

    for columna in exposiciones:
        if columna not in datos.columns:
            continue

        ruta = (
            ruta_base
            / f"{columna}_strike.png"
        )

        resultados[
            f"{columna}_strike"
        ] = str(
            graficar_exposicion_strike(
                cadena=datos,
                ticker=ticker,
                columna=columna,
                spot=spot,
                ruta_salida=ruta,
            )
        )

    if "open_interest" in datos.columns:
        ruta = (
            ruta_base
            / "open_interest_strike.png"
        )

        resultados[
            "open_interest"
        ] = str(
            graficar_oi_strike(
                cadena=datos,
                ticker=ticker,
                spot=spot,
                ruta_salida=ruta,
            )
        )

    for valor in [
        "iv",
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "charm",
    ]:
        if valor not in datos.columns:
            continue

        for tipo in [
            "CALL",
            "PUT",
        ]:
            try:
                ruta = (
                    ruta_base
                    / (
                        f"{valor}_surface_"
                        f"{tipo.lower()}.html"
                    )
                )

                resultados[
                    f"{valor}_surface_"
                    f"{tipo.lower()}"
                ] = str(
                    graficar_superficie_3d(
                        cadena=datos,
                        ticker=ticker,
                        valor=valor,
                        tipo=tipo,
                        spot=spot,
                        ruta_salida=ruta,
                    )
                )

            except ValueError:
                continue

    return resultados