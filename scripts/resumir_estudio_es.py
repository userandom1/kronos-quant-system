"""Muestra en terminal los niveles GEX/DEX del escenario SPX → ES."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from options_flow.estudios_es import calcular_estudio


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path)
    args = parser.parse_args()
    carpeta = args.carpeta
    meta = json.loads((carpeta / "metadatos.json").read_text(encoding="utf-8"))
    if meta["subyacente_precio"] != "ES" or meta["subyacente_opciones"] != "SPX":
        raise ValueError("Se requieren ES y SPX identificados por separado")
    with (carpeta / "opciones_spx.csv").open(newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    niveles = calcular_estudio(
        filas, spx_referencia=float(meta["spx_referencia"]),
        es_referencia=float(meta["es_referencia"]),
        spx_hora_utc=meta["spx_hora_utc"], es_hora_utc=meta["es_hora_utc"],
    )
    print(f"Datos: {meta['estado_datos']} | Precio: ES | Opciones: SPX | {meta['fuente']}")
    print("Escenario dealer HIPOTÉTICO: calls cortas, puts largas")
    print("Strike SPX | Nivel ES proxy | GEX millones USD/1% | DEX millones USD")
    for fila in niveles:
        print(
            f"{fila['strike_spx']:10.2f} | {fila['nivel_es_proxy']:14.2f} | "
            f"{fila['gex_usd_por_1pct']/1_000_000:20.3f} | "
            f"{fila['dex_usd']/1_000_000:16.3f}"
        )


if __name__ == "__main__":
    main()
