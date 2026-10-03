"""Revalida opciones históricas sin red y sin modificar los snapshots fuente."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from core.serializacion import serializar_json
from motor_mercado.deep_research_activo import RUTA_BASE, _revision_codigo
from motor_opciones.calidad_cadena import evaluar_calidad_cadena
from motor_opciones.dealer_por_vencimiento import analizar_dealer_por_vencimiento
from motor_opciones.dealer_universal import calcular_exposiciones_dealer, resumir_dealer
from motor_opciones.griegas_universales import aplicar_griegas
from motor_opciones.movimiento_esperado import calcular_movimiento_esperado


def reprocesar(origen: Path, destino: Path) -> dict[str, object]:
    """Conserva spot y DTE históricos; reconcilia totales por expiración."""
    cadena = pd.read_csv(origen / "cadena_opciones.csv")
    spots = cadena["spot"].dropna().unique()
    if len(spots) != 1 or not np.isfinite(spots[0]) or spots[0] <= 0:
        raise ValueError(f"Spot histórico ambiguo o inválido: {origen}")
    spot = float(spots[0])
    valida, rechazada, calidad = evaluar_calidad_cadena(cadena)
    if valida.empty:
        raise ValueError(f"No hay contratos válidos en {origen}")
    valida = calcular_exposiciones_dealer(aplicar_griegas(valida, spot), spot)
    total = resumir_dealer(valida)
    tabla, perfil = analizar_dealer_por_vencimiento(valida, spot)
    movimientos = calcular_movimiento_esperado(cadena, spot)
    for columna in ("net_gex_1pct", "net_dex", "net_vega_1pt", "net_vanna_1pt", "net_charm_dia"):
        if not np.isclose(tabla[columna].sum(), total[columna], rtol=1e-10, atol=1e-5):
            raise AssertionError(f"No reconcilia {columna}: {origen}")
    destino.mkdir(parents=True, exist_ok=False)
    valida.to_csv(destino / "cadena_opciones.csv", index=False)
    rechazada.to_csv(destino / "contratos_rechazados.csv", index=False)
    exportable = tabla.copy()
    exportable["gamma_flips"] = exportable["gamma_flips"].map(json.dumps)
    exportable.to_csv(destino / "dealer_por_vencimiento.csv", index=False)
    perfil.to_csv(destino / "perfil_gamma_por_vencimiento.csv", index=False)
    movimientos.to_csv(destino / "expected_move_por_vencimiento.csv", index=False)
    informe = {
        "modo": "REPROCESADO_HISTORICO_SIN_RED", "origen": str(origen.resolve()),
        "fecha_snapshot": origen.name, "ticker": origen.parent.name, "spot_historico": spot,
        "calidad": calidad, "dealer": total,
        "dealer_por_vencimiento": tabla.to_dict(orient="records"),
        "expected_move_por_vencimiento": movimientos.to_dict(orient="records"),
        "reconciliacion": "OK", "revision": _revision_codigo(),
        "advertencia": "Se conserva el DTE original. No es una cotización actual; la antigüedad de bid/ask no está verificada.",
    }
    (destino / "auditoria.json").write_text(json.dumps(
        serializar_json(informe), ensure_ascii=False, indent=2, allow_nan=False
    ), encoding="utf-8")
    return {"ticker": origen.parent.name, "origen": str(origen),
            "contratos_originales": len(cadena), "contratos_validos": len(valida),
            "contratos_rechazados": len(rechazada), "vencimientos": len(tabla),
            "gamma_flips": sum(map(len, tabla["gamma_flips"])),
            "expected_move_validos": int((movimientos["estado"] == "OK").sum()),
            "expected_move_no_disponibles": int((movimientos["estado"] != "OK").sum()),
            "call_wall": total["call_wall"], "put_wall": total["put_wall"],
            "reconciliacion": "OK"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="*", default=["SPY", "QQQ", "IWM", "XLK", "SMH"])
    parser.add_argument("--fecha", help="Prefijo YYYYMMDD del snapshot histórico")
    args = parser.parse_args()
    if args.fecha and (len(args.fecha) != 8 or not args.fecha.isdigit()):
        raise ValueError("La fecha debe tener formato YYYYMMDD.")
    salida = RUTA_BASE / "resultados" / "auditoria_v21" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    filas = []
    for ticker in args.tickers:
        # Solo se aceptan nombres de carpetas de activos, sin segmentos de ruta.
        if not ticker or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for c in ticker):
            raise ValueError(f"Ticker no válido: {ticker}")
        patron = f"{args.fecha or ''}*/cadena_opciones.csv"
        fuentes = sorted((RUTA_BASE / "resultados" / "deep_research" / ticker).glob(patron))
        if not fuentes:
            raise FileNotFoundError(f"No hay snapshots para {ticker}")
        filas.append(reprocesar(fuentes[-1].parent, salida / ticker))
    tabla = pd.DataFrame(filas)
    tabla.to_csv(salida / "resumen_auditoria.csv", index=False)
    print(tabla.to_string(index=False))
    print(f"Auditoría: {salida}")


if __name__ == "__main__":
    main()
