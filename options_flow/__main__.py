"""Entrada de terminal para comprobar capturas de opciones."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .capturas import cargar_captura
from .griegas import SupuestosGriegas, calcular_griegas_captura


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Análisis de opciones desde terminal")
    comandos = parser.add_subparsers(dest="comando", required=True)
    validar = comandos.add_parser("validar", help="Comprobar una captura")
    griegas = comandos.add_parser("griegas", help="Calcular Delta y Gamma por contrato")
    for comando in (validar, griegas):
        comando.add_argument("metadatos", type=Path, help="Archivo JSON de metadatos")
        comando.add_argument("contratos", type=Path, help="Archivo CSV de contratos")
    griegas.add_argument("--tasa-anual", type=float, required=True, help="Tasa continua anual, decimal")
    griegas.add_argument("--dividendo-anual", type=float, required=True, help="Rendimiento continuo anual, decimal")
    argumentos = sys.argv[1:]
    if argumentos and argumentos[0] not in {"validar", "griegas", "-h", "--help"}:
        argumentos = ["validar", *argumentos]
    args = parser.parse_args(argumentos)
    try:
        captura = cargar_captura(args.metadatos, args.contratos)
        supuestos = (
            SupuestosGriegas(args.tasa_anual, args.dividendo_anual)
            if args.comando == "griegas" else None
        )
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
    if args.comando == "validar":
        return 0 if captura.contratos else 2

    resultados, omitidos = calcular_griegas_captura(captura, supuestos)
    print("Modelo: Black-Scholes-Merton europeo (aproximación para opciones americanas)")
    print(f"Tasa anual: {supuestos.tasa_anual:.6f} | dividendo anual: {supuestos.dividendo_anual:.6f}")
    print("Delta: cambio de prima por 1 unidad de spot; Gamma: cambio de Delta por 1 unidad de spot")
    print("Resultados por unidad del subyacente; multiplicador aún no aplicado")
    print(f"Greeks calculados: {len(resultados)} | omitidos: {len(omitidos)}")
    for fila in resultados:
        print(
            f"{fila.id_contrato} {fila.tipo} V={fila.vencimiento} "
            f"S={fila.spot:g} K={fila.strike:g} "
            f"IV={fila.volatilidad:.6f} M={fila.multiplicador} "
            f"Delta={fila.delta:.8f} Gamma={fila.gamma:.8f} "
            f"T={fila.tiempo_anos:.8f} años ({fila.precision_tiempo})"
        )
    for fila in omitidos:
        print(f"{fila.id_contrato}: OMITIDO ({fila.motivo})")
    return 0 if resultados else 2


if __name__ == "__main__":
    raise SystemExit(main())
