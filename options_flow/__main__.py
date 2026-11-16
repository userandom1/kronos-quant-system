"""Entrada de terminal para comprobar capturas de opciones."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .capturas import cargar_captura
from .ejecucion import EntradaCaptura, ejecutar_y_guardar
from .griegas import SupuestosGriegas, calcular_griegas_captura
from .proveedor_yfinance import capturar_yfinance


def _ejecutar_analisis(args: argparse.Namespace) -> int:
    if bool(args.en_vivo) == bool(args.metadatos or args.contratos):
        raise ValueError("Indica --en-vivo o el par --metadatos/--contratos")
    if not args.en_vivo and (args.metadatos is None or args.contratos is None):
        raise ValueError("Se necesitan --metadatos y --contratos juntos")
    if args.anterior_ejecucion and (args.anterior_metadatos or args.anterior_contratos):
        raise ValueError("Usa una sola forma de indicar la captura anterior")
    if bool(args.anterior_metadatos) != bool(args.anterior_contratos):
        raise ValueError("La captura anterior necesita JSON y CSV")
    if args.max_filas < 0:
        raise ValueError("max_filas_debe_ser_no_negativo")

    if args.en_vivo:
        vivo = capturar_yfinance(
            args.en_vivo,
            tuple(args.vencimiento),
            max_vencimientos=args.max_vencimientos,
        )
        actual = EntradaCaptura(
            vivo.metadatos_json, vivo.contratos_csv, vivo.proveedor_original_json
        )
        print(f"Captura en vivo: {args.en_vivo} | vencimientos: {', '.join(vivo.vencimientos)}")
    else:
        actual = EntradaCaptura.desde_archivos(args.metadatos, args.contratos)

    anterior = None
    if args.anterior_ejecucion:
        anterior = EntradaCaptura.desde_archivos(
            args.anterior_ejecucion / "actual_metadatos.json",
            args.anterior_ejecucion / "actual_contratos.csv",
        )
    elif args.anterior_metadatos:
        anterior = EntradaCaptura.desde_archivos(
            args.anterior_metadatos, args.anterior_contratos
        )
    ejecucion = ejecutar_y_guardar(
        actual,
        SupuestosGriegas(args.tasa_anual, args.dividendo_anual),
        args.salida,
        entrada_anterior=anterior,
        incluir_escenario_dealer=args.escenario_dealer,
    )
    analisis = ejecucion.analisis
    captura = analisis.actual
    print(f"Ejecución: {ejecucion.ruta}")
    print(f"Huella reproducible: {ejecucion.huella_analisis}")
    print(
        f"{captura.metadatos.subyacente} | {captura.metadatos.capturado_en_utc.isoformat()} "
        f"| {captura.total_filas} contratos, {len(captura.contratos)} válidos, "
        f"{len(captura.rechazos)} rechazados"
    )
    print(
        f"Spot: {captura.metadatos.spot} {captura.metadatos.divisa} "
        f"| observado: {captura.metadatos.spot_observado_en_utc or 'DESCONOCIDO'} "
        f"| fuente: {captura.metadatos.fuente_spot}"
    )
    print(
        "Hora de cotización desconocida: "
        f"{sum(c.cotizacion_utc is None for c in captura.contratos)}; "
        "la hora de descarga no certifica frescura bid/ask"
    )
    print(f"Delta/Gamma: {len(analisis.griegas)} calculados, {len(analisis.omitidos)} omitidos")
    if analisis.omitidos:
        motivos: dict[str, int] = {}
        for fila in analisis.omitidos:
            motivos[fila.motivo] = motivos.get(fila.motivo, 0) + 1
        print(f"Motivos de omisión: {motivos}")
    if captura.rechazos:
        motivos_rechazo: dict[str, int] = {}
        for fila in captura.rechazos:
            for motivo in fila.motivos:
                motivos_rechazo[motivo] = motivos_rechazo.get(motivo, 0) + 1
        print(f"Motivos de rechazo: {motivos_rechazo}")
    print("Agregados por vencimiento y tipo (OI conocido; hipótesis contratos largos):")
    for fila in analisis.por_vencimiento:
        print(
            f"  {fila.vencimiento} {fila.tipo}: OI={fila.oi_conocido} "
            f"cobertura={fila.contratos_con_oi}/{fila.contratos_con_griegas} "
            f"Delta×OI×M={fila.delta_oi_unidades} "
            f"Gamma×OI×M={fila.gamma_oi_unidades_por_precio}"
        )
    if analisis.escenario_vencimiento is not None:
        print("Escenario dealer HIPOTÉTICO: calls cortas, puts largas:")
        for fila in analisis.escenario_vencimiento:
            print(
                f"  {fila.vencimiento}: Delta={fila.delta_oi_unidades} "
                f"Gamma={fila.gamma_oi_unidades_por_precio} "
                f"cobertura={fila.contratos_con_oi}/{fila.contratos_con_griegas}"
            )
    if analisis.actividad is not None:
        print("Actividad estimada entre capturas; no son operaciones individuales:")
        estados: dict[str, int] = {}
        for fila in analisis.actividad.contratos:
            estados[fila.estado_volumen] = estados.get(fila.estado_volumen, 0) + 1
        print(f"  Misma fecha de mercado: {analisis.actividad.misma_fecha_mercado}")
        print(f"  Estados: {estados}")
        print(f"  Contratos desaparecidos: {len(analisis.actividad.contratos_desaparecidos)}")
        print("  Resumen por vencimiento y tipo:")
        for fila in analisis.actividad_por_vencimiento:
            print(
                f"    {fila.vencimiento} {fila.tipo}: "
                f"Δvol={fila.incremento_volumen_estimado} "
                f"cobertura={fila.contratos_comparables}/{fila.contratos_actuales} "
                f"prima_mid_estimativa={fila.prima_mid_estimativa}"
            )
        comparables = sorted(
            (f for f in analisis.actividad.contratos if f.incremento_volumen_estimado is not None),
            key=lambda f: (-f.incremento_volumen_estimado, f.id_contrato),
        )
        for fila in comparables[:args.max_filas]:
            print(
                f"  {fila.id_contrato}: Δvol={fila.incremento_volumen_estimado} "
                f"ΔOI_reportado={fila.cambio_oi_reportado} "
                f"prima_mid_estimativa={fila.prima_mid_estimativa}"
            )
        if len(comparables) > args.max_filas:
            print(f"  {len(comparables) - args.max_filas} filas comparables más en actividad.csv")
    print("Tablas completas y entradas originales: archivos CSV/JSON en la carpeta de ejecución")
    return 0 if analisis.griegas else 2


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Análisis de opciones desde terminal")
    comandos = parser.add_subparsers(dest="comando", required=True)
    validar = comandos.add_parser("validar", help="Comprobar una captura")
    griegas = comandos.add_parser("griegas", help="Calcular Delta y Gamma por contrato")
    analizar = comandos.add_parser("analizar", help="Análisis completo y reproducible")
    for comando in (validar, griegas):
        comando.add_argument("metadatos", type=Path, help="Archivo JSON de metadatos")
        comando.add_argument("contratos", type=Path, help="Archivo CSV de contratos")
    griegas.add_argument("--tasa-anual", type=float, required=True, help="Tasa continua anual, decimal")
    griegas.add_argument("--dividendo-anual", type=float, required=True, help="Rendimiento continuo anual, decimal")
    analizar.add_argument("--en-vivo", metavar="SIMBOLO", help="Capturar cadena desde yfinance")
    analizar.add_argument("--vencimiento", action="append", default=[], help="Fecha YYYY-MM-DD; repetible")
    analizar.add_argument("--max-vencimientos", type=int, default=3, help="Cantidad automática; defecto 3")
    analizar.add_argument("--metadatos", type=Path, help="JSON de captura actual guardada")
    analizar.add_argument("--contratos", type=Path, help="CSV de captura actual guardada")
    analizar.add_argument("--anterior-ejecucion", type=Path, help="Carpeta de ejecución previa")
    analizar.add_argument("--anterior-metadatos", type=Path, help="JSON previo")
    analizar.add_argument("--anterior-contratos", type=Path, help="CSV previo")
    analizar.add_argument("--tasa-anual", type=float, required=True)
    analizar.add_argument("--dividendo-anual", type=float, required=True)
    analizar.add_argument("--escenario-dealer", action="store_true", help="Escenario hipotético calls cortas/puts largas")
    analizar.add_argument("--salida", type=Path, default=Path(__file__).resolve().parents[1] / "resultados" / "analisis")
    analizar.add_argument("--max-filas", type=int, default=20, help="Filas de actividad mostradas")
    argumentos = sys.argv[1:]
    if argumentos and argumentos[0] not in {"validar", "griegas", "analizar", "-h", "--help"}:
        argumentos = ["validar", *argumentos]
    args = parser.parse_args(argumentos)
    if args.comando == "analizar":
        try:
            return _ejecutar_analisis(args)
        except Exception as error:
            print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
            return 1
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
