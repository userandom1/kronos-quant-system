"""Entrada de terminal para comprobar capturas de opciones."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .capturas import cargar_captura


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Valida una captura de cadena de opciones")
    parser.add_argument("metadatos", type=Path, help="Archivo JSON de metadatos")
    parser.add_argument("contratos", type=Path, help="Archivo CSV de contratos")
    args = parser.parse_args()
    try:
        captura = cargar_captura(args.metadatos, args.contratos)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Captura: {captura.metadatos.id_captura}")
    print(f"Activo: {captura.metadatos.subyacente}")
    print(f"Proveedor: {captura.metadatos.proveedor}")
    print(f"Hora UTC: {captura.metadatos.capturado_en_utc.isoformat()}")
    print(f"Contratos: {captura.total_filas} | válidos: {len(captura.contratos)} | rechazados: {len(captura.rechazos)}")
    print(f"Sin hora de cotización: {sum(c.cotizacion_utc is None for c in captura.contratos)}")
    print(
        "No aptos para Greeks por tiempo: "
        f"{sum(c.impedimento_griegas(captura.metadatos.capturado_en_utc, captura.metadatos.zona_mercado) is not None for c in captura.contratos)}"
    )
    for rechazo in captura.rechazos:
        print(f"Línea {rechazo.linea_csv}: {', '.join(rechazo.motivos)}")
    print(f"SHA256 CSV: {captura.sha256_csv}")
    print(f"SHA256 metadatos: {captura.sha256_metadatos}")
    return 0 if captura.contratos else 2


if __name__ == "__main__":
    raise SystemExit(main())
