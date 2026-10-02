"""Controles de cotización comunes al motor universal y Deep Research."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PoliticaCalidadOpciones:
    """Umbrales explícitos; no certifican actualidad ni ejecutabilidad."""

    iv_minima: float = 0.0001
    iv_maxima: float = 5.0
    spread_relativo_maximo: float = 1.0


def evaluar_calidad_cadena(
    cadena: pd.DataFrame,
    politica: PoliticaCalidadOpciones | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Separa contratos utilizables y rechazados, conservando sus motivos.

    Un DTE cero sin hora exacta de expiración se excluye: no se inventa un
    día de vida. Se permiten DTE fraccionarios positivos aportados por datos
    con esa precisión. Un bid cero no invalida por sí solo, pero el spread sí.
    """
    politica = politica or PoliticaCalidadOpciones()
    datos = cadena.copy().reset_index(drop=True)
    columnas = ["strike", "bid", "ask", "iv", "dte", "open_interest"]
    faltantes = set(columnas + ["tipo_opcion", "vencimiento"]) - set(datos)
    if faltantes:
        raise ValueError(f"Faltan columnas de opciones: {sorted(faltantes)}")
    for columna in columnas:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
    datos["tipo_opcion"] = datos["tipo_opcion"].astype(str).str.upper()
    mid = (datos["ask"] + datos["bid"]) / 2
    spread = (datos["ask"] - datos["bid"]) / mid.where(mid > 0)
    motivos = {
        "dato_no_finito": ~np.isfinite(datos[columnas]).all(axis=1),
        "strike_invalido": datos["strike"] <= 0,
        "cotizacion_invalida": (datos["bid"] < 0) | (datos["ask"] <= 0),
        "mercado_cruzado": datos["bid"] > datos["ask"],
        "spread_excesivo": spread > politica.spread_relativo_maximo,
        "iv_invalida": ~datos["iv"].between(
            politica.iv_minima, politica.iv_maxima, inclusive="neither"
        ),
        "dte_no_positivo": datos["dte"] <= 0,
        "oi_negativo": datos["open_interest"] < 0,
        "tipo_invalido": ~datos["tipo_opcion"].isin(["CALL", "PUT"]),
        "vencimiento_invalido": pd.to_datetime(
            datos["vencimiento"], errors="coerce"
        ).isna(),
        "duplicado": datos.duplicated(
            subset=["vencimiento", "strike", "tipo_opcion"], keep="first"
        ),
    }
    flags = pd.DataFrame(motivos, index=datos.index).fillna(True)
    rechazado = flags.any(axis=1)
    descartados = datos.loc[rechazado].copy()
    descartados["motivos_calidad"] = [
        ";".join(fila.index[fila]) for _, fila in flags.loc[rechazado].iterrows()
    ]
    validos = datos.loc[~rechazado].copy()
    informe = {
        "contratos_entrada": len(datos),
        "contratos_validos": len(validos),
        "contratos_rechazados": len(descartados),
        "motivos": {nombre: int(mask.sum()) for nombre, mask in motivos.items()},
        "actualidad_cotizacion": "NO_VERIFICADA",
        "politica_0dte": "Excluir sin tiempo positivo hasta expiración",
    }
    validos.attrs["calidad"] = informe
    return validos, descartados, informe
