"""Exposiciones y cruces de Gamma por vencimiento sobre la cadena universal."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from motor_opciones.dealer_universal import resumir_dealer, signo_dealer


def buscar_cruces_gamma(spots: np.ndarray, gex: np.ndarray) -> list[float]:
    """Interpola cruces interiores; una curva nula no representa infinitos flips."""
    spots = np.asarray(spots, dtype=float)
    gex = np.asarray(gex, dtype=float)
    if (len(spots) != len(gex) or len(spots) < 2
            or not np.isfinite(spots).all() or not np.isfinite(gex).all()
            or not (np.diff(spots) > 0).all()):
        raise ValueError("El perfil necesita puntos finitos, ordenados y únicos.")
    no_cero = np.flatnonzero(gex != 0)
    cruces = []
    for izquierda, derecha in zip(no_cero[:-1], no_cero[1:]):
        if np.sign(gex[izquierda]) == np.sign(gex[derecha]):
            continue
        x0, x1 = spots[izquierda], spots[derecha]
        y0, y1 = gex[izquierda], gex[derecha]
        cruces.append(float(x0 - y0 * (x1 - x0) / (y1 - y0)))
    return cruces


def analizar_dealer_por_vencimiento(
    cadena: pd.DataFrame,
    spot: float,
    rango_pct: float = 0.20,
    puntos: int = 161,
    tipo_interes: float = 0.04,
    dividendo: float = 0.01,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve resumen y perfil por fecha, conservando todos los flips.

    Revalúa Gamma con IV fija dentro de ±rango_pct del spot. SIN_CRUCE solo
    describe esa malla; no garantiza la inexistencia de cruces fuera de ella
    ni entre puntos muy próximos. Convención proxy: calls short, puts long.
    """
    if not np.isfinite(spot) or spot <= 0 or not 0 < rango_pct < 1 or puntos < 3:
        raise ValueError("Spot, rango o resolución de Gamma no válidos.")
    if cadena.empty:
        raise ValueError("Cadena vacía para dealer por vencimiento.")
    datos = cadena.copy()
    datos["vencimiento"] = pd.to_datetime(datos["vencimiento"], errors="raise").dt.normalize()
    numericas = datos[["strike", "iv", "dte", "open_interest"]]
    if (not np.isfinite(numericas).all().all()
            or (numericas[["strike", "iv", "dte"]] <= 0).any().any()
            or (datos["open_interest"] < 0).any()):
        raise ValueError("Dealer requiere contratos con IV y DTE positivos y OI válido.")
    eje = np.linspace(spot * (1 - rango_pct), spot * (1 + rango_pct), puntos)
    resumenes, perfiles = [], []
    for fecha, grupo in datos.groupby("vencimiento", sort=True):
        strike = grupo["strike"].to_numpy(dtype=float)
        iv = grupo["iv"].to_numpy(dtype=float)
        tiempo = grupo["dte"].to_numpy(dtype=float) / 365.0
        raiz = np.sqrt(tiempo)
        oi = grupo["open_interest"].to_numpy(dtype=float)
        signo = signo_dealer(grupo["tipo_opcion"])

        def gex_en(precio: float) -> float:
            d1 = (np.log(precio / strike) + (tipo_interes - dividendo + 0.5 * iv**2) * tiempo) / (iv * raiz)
            gamma = np.exp(-dividendo * tiempo) * norm.pdf(d1) / (precio * iv * raiz)
            return float(np.sum(signo * gamma * oi * 100.0 * precio**2 * 0.01))

        valores = np.array([gex_en(precio) for precio in eje])
        flips = buscar_cruces_gamma(eje, valores)
        # Refinar las raíces de intervalos con cambio de signo en el propio modelo.
        for i, (izq, der) in enumerate(zip(eje[:-1], eje[1:])):
            if valores[i] != 0 and valores[i + 1] != 0 and np.sign(valores[i]) != np.sign(valores[i + 1]):
                aproximado = izq - valores[i] * (der - izq) / (valores[i + 1] - valores[i])
                j = int(np.argmin(np.abs(np.asarray(flips) - aproximado)))
                flips[j] = float(brentq(gex_en, izq, der))
        fecha_texto = fecha.date().isoformat()
        estado = "UNICO" if len(flips) == 1 else "MULTIPLE" if flips else "SIN_CRUCE"
        if np.all(valores == 0):
            estado = "SIN_EXPOSICION"
        resumenes.append({
            "vencimiento": fecha_texto,
            "dte": float(grupo["dte"].min()),
            "contratos": len(grupo),
            **resumir_dealer(grupo),
            "gamma_flip": flips[0] if len(flips) == 1 else None,
            "gamma_flips": flips,
            "estado_gamma_flip": estado,
            "rango_spot_min": float(eje[0]),
            "rango_spot_max": float(eje[-1]),
            "puntos_perfil": puntos,
            "metodo": "BSM_IV_FIJA_PROXY_CALL_SHORT_PUT_LONG",
        })
        perfiles.extend({"vencimiento": fecha_texto, "spot": float(x), "net_gex_1pct": float(y)}
                        for x, y in zip(eje, valores))
    return pd.DataFrame(resumenes), pd.DataFrame(perfiles)
