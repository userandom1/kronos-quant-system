"""Estimaciones de movimiento por vencimiento a partir de opciones ATM."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from motor_opciones.calidad_cadena import evaluar_calidad_cadena


@dataclass(frozen=True)
class PoliticaMovimientoEsperado:
    """Distancia ATM máxima respecto al spot; DTE en días calendario."""

    distancia_atm_maxima: float = 0.02


def calcular_movimiento_esperado(
    cadena: pd.DataFrame,
    spot: float,
    politica: PoliticaMovimientoEsperado | None = None,
    rechazados: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Devuelve straddle mid e IV media ATM, sin asignar probabilidades.

    Se elige el strike original más cercano al spot (empate: menor strike).
    Ambos contratos deben superar calidad y compartir fecha, strike y DTE.
    Los rechazos originales permiten detectar una pareja ATM incompleta,
    aunque otras parejas más lejanas estén disponibles. No usa la columna
    mid proporcionada: calcula mid desde bid/ask. Límites centrados en spot;
    no son breakevens del straddle ni un intervalo de confianza calibrado.
    """
    politica = politica or PoliticaMovimientoEsperado()
    if not np.isfinite(spot) or spot <= 0:
        raise ValueError("Spot debe ser finito y positivo.")
    if not np.isfinite(politica.distancia_atm_maxima) or not 0 <= politica.distancia_atm_maxima < 1:
        raise ValueError("Distancia ATM máxima fuera de [0, 1).")
    partes = [cadena.copy()]
    if rechazados is not None and not rechazados.empty:
        partes.append(rechazados.copy())
    for parte in partes:
        parte.attrs = {}
    datos = pd.concat(partes, ignore_index=True)
    # Normalizar fechas antes de comprobar duplicados o formar las parejas.
    if "vencimiento" not in datos:
        raise ValueError("Falta vencimiento en la cadena.")
    datos["vencimiento"] = pd.to_datetime(
        datos["vencimiento"], errors="coerce", format="mixed", utc=True
    ).dt.tz_localize(None).dt.normalize()
    validos, _, calidad = evaluar_calidad_cadena(datos)
    datos["strike"] = pd.to_numeric(datos["strike"], errors="coerce")
    fechas = sorted(datos["vencimiento"].dropna().unique())
    if not fechas:
        raise ValueError("No hay vencimientos válidos para Expected Move.")
    filas = []
    for fecha in fechas:
        original = datos.loc[datos["vencimiento"] == fecha]
        grupo = validos.loc[validos["vencimiento"] == fecha]
        strikes = original.loc[np.isfinite(original["strike"]) & (original["strike"] > 0), "strike"].unique()
        fila = {
            "vencimiento": pd.Timestamp(fecha).date().isoformat(), "spot": float(spot),
            "estado": "SIN_CONTRATOS_VALIDOS", "motivo": "No hay contratos utilizables.",
            "strike_atm": None, "distancia_atm_pct": None, "dte": None,
            "call_mid": None, "put_mid": None, "call_spread_pct": None,
            "put_spread_pct": None, "iv_call": None, "iv_put": None, "iv_atm": None,
            "call_contract_symbol": None, "put_contract_symbol": None,
            "move_straddle_dolares": None, "move_straddle_pct": None,
            "limite_inferior_straddle": None, "limite_superior_straddle": None,
            "move_iv_dolares": None, "move_iv_pct": None,
            "limite_inferior_iv": None, "limite_superior_iv": None,
            "contratos_entrada": len(original), "contratos_validos": len(grupo),
            "contratos_rechazados": len(original) - len(grupo),
            "metodo_straddle": "CALL_MID_MAS_PUT_MID", "metodo_iv": "SPOT_IV_MEDIA_SQRT_DTE_365",
            "base_dias_anual": 365, "actualidad_cotizacion": "NO_VERIFICADA",
        }
        if len(strikes):
            strike = float(min(strikes, key=lambda k: (abs(k - spot), k)))
            distancia = abs(strike - spot) / spot
            fila.update(strike_atm=strike, distancia_atm_pct=distancia)
            pareja = grupo.loc[grupo["strike"] == strike]
            if distancia > politica.distancia_atm_maxima:
                fila.update(estado="ATM_LEJANO", motivo="El strike más cercano supera la distancia ATM permitida.")
            elif not grupo.empty:
                if set(pareja["tipo_opcion"]) != {"CALL", "PUT"}:
                    fila.update(estado="SIN_PAREJA_ATM", motivo="Falta call o put válida en el strike ATM original.")
                else:
                    call = pareja.loc[pareja["tipo_opcion"] == "CALL"].iloc[0]
                    put = pareja.loc[pareja["tipo_opcion"] == "PUT"].iloc[0]
                    if not np.isclose(call["dte"], put["dte"], rtol=0, atol=1e-6):
                        fila.update(estado="DTE_INCONSISTENTE", motivo="La pareja ATM tiene tiempos a vencimiento distintos.")
                    else:
                        dte = float((call["dte"] + put["dte"]) / 2)
                        call_mid = float((call["bid"] + call["ask"]) / 2)
                        put_mid = float((put["bid"] + put["ask"]) / 2)
                        iv_atm = float((call["iv"] + put["iv"]) / 2)
                        straddle = call_mid + put_mid
                        move_iv = float(spot * iv_atm * np.sqrt(dte / 365))
                        fila.update(
                            estado="OK", motivo="Pareja ATM válida; estimaciones bajo hipótesis.",
                            dte=dte, call_mid=call_mid, put_mid=put_mid,
                            call_spread_pct=float((call["ask"] - call["bid"]) / call_mid),
                            put_spread_pct=float((put["ask"] - put["bid"]) / put_mid),
                            iv_call=float(call["iv"]), iv_put=float(put["iv"]), iv_atm=iv_atm,
                            call_contract_symbol=call.get("contract_symbol"),
                            put_contract_symbol=put.get("contract_symbol"),
                            move_straddle_dolares=straddle, move_straddle_pct=straddle / spot,
                            limite_inferior_straddle=spot - straddle, limite_superior_straddle=spot + straddle,
                            move_iv_dolares=move_iv, move_iv_pct=move_iv / spot,
                            limite_inferior_iv=spot - move_iv, limite_superior_iv=spot + move_iv,
                        )
                        if not np.isfinite([straddle, move_iv, spot + straddle, spot + move_iv]).all():
                            raise ValueError("Expected Move fuera del rango numérico finito.")
        filas.append(fila)
    resultado = pd.DataFrame(filas)
    resultado.attrs["calidad"] = calidad
    resultado.attrs["politica"] = {"distancia_atm_maxima": politica.distancia_atm_maxima}
    return resultado
