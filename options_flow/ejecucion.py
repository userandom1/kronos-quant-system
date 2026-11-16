"""Orquestación y persistencia reproducible de análisis de opciones."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path

from .actividad import (
    ActividadAgregada, ActividadContrato, ComparacionCapturas,
    agregar_actividad, comparar_capturas,
)
from .agregados import AgregadoGriegas, EscenarioDealer, agregar_griegas, escenario_dealer
from .capturas import CapturaValidada, Rechazo, validar_captura_bytes
from .griegas import (
    OmitidoGriegas, ResultadoGriegas, SupuestosGriegas, calcular_griegas_captura,
)


@dataclass(frozen=True)
class EntradaCaptura:
    metadatos_json: bytes
    contratos_csv: bytes
    proveedor_original_json: bytes | None = None

    @classmethod
    def desde_archivos(cls, metadatos: Path, contratos: Path) -> EntradaCaptura:
        return cls(metadatos.read_bytes(), contratos.read_bytes())


@dataclass(frozen=True)
class Analisis:
    actual: CapturaValidada
    anterior: CapturaValidada | None
    griegas: tuple[ResultadoGriegas, ...]
    omitidos: tuple[OmitidoGriegas, ...]
    por_strike: tuple[AgregadoGriegas, ...]
    por_vencimiento: tuple[AgregadoGriegas, ...]
    actividad: ComparacionCapturas | None
    actividad_por_strike: tuple[ActividadAgregada, ...] | None
    actividad_por_vencimiento: tuple[ActividadAgregada, ...] | None
    escenario_strike: tuple[EscenarioDealer, ...] | None
    escenario_vencimiento: tuple[EscenarioDealer, ...] | None
    supuestos: SupuestosGriegas


@dataclass(frozen=True)
class EjecucionGuardada:
    ruta: Path
    huella_analisis: str
    analisis: Analisis


def analizar(
    actual: CapturaValidada,
    supuestos: SupuestosGriegas,
    *,
    anterior: CapturaValidada | None = None,
    incluir_escenario_dealer: bool = False,
) -> Analisis:
    griegas, omitidos = calcular_griegas_captura(actual, supuestos)
    por_strike = agregar_griegas(actual, griegas, por_strike=True)
    por_vencimiento = agregar_griegas(actual, griegas, por_strike=False)
    actividad = comparar_capturas(anterior, actual) if anterior is not None else None
    return Analisis(
        actual=actual,
        anterior=anterior,
        griegas=griegas,
        omitidos=omitidos,
        por_strike=por_strike,
        por_vencimiento=por_vencimiento,
        actividad=actividad,
        actividad_por_strike=agregar_actividad(actividad, por_strike=True) if actividad else None,
        actividad_por_vencimiento=agregar_actividad(actividad, por_strike=False) if actividad else None,
        escenario_strike=escenario_dealer(por_strike) if incluir_escenario_dealer else None,
        escenario_vencimiento=escenario_dealer(por_vencimiento) if incluir_escenario_dealer else None,
        supuestos=supuestos,
    )


def _json_default(valor: object) -> object:
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    if is_dataclass(valor):
        return asdict(valor)
    raise TypeError(f"Tipo no serializable: {type(valor).__name__}")


def _json_bytes(datos: object) -> bytes:
    return (json.dumps(
        datos, default=_json_default, ensure_ascii=False, sort_keys=True,
        indent=2, allow_nan=False,
    ) + "\n").encode("utf-8")


def _csv_dataclasses(filas: tuple[object, ...], clase: type) -> bytes:
    salida = StringIO(newline="")
    nombres = [campo.name for campo in fields(clase)]
    escritor = csv.DictWriter(salida, fieldnames=nombres, lineterminator="\n")
    escritor.writeheader()
    for fila in filas:
        valores = asdict(fila)
        escritor.writerow({
            nombre: "" if valor is None else valor
            for nombre, valor in valores.items()
        })
    return salida.getvalue().encode("utf-8")


def _csv_rechazos(rechazos: tuple[Rechazo, ...]) -> bytes:
    salida = StringIO(newline="")
    escritor = csv.DictWriter(
        salida, fieldnames=["linea_csv", "id_contrato", "motivos", "fila_original_json"],
        lineterminator="\n",
    )
    escritor.writeheader()
    for rechazo in rechazos:
        escritor.writerow({
            "linea_csv": rechazo.linea_csv,
            "id_contrato": rechazo.fila_original.get("id_contrato", ""),
            "motivos": ";".join(rechazo.motivos),
            "fila_original_json": json.dumps(rechazo.fila_original, ensure_ascii=False),
        })
    return salida.getvalue().encode("utf-8")


def _contenido_analisis(analisis: Analisis) -> dict[str, object]:
    codigo = Path(__file__).resolve().parent
    piezas = [
        f"{archivo.name}:{hashlib.sha256(archivo.read_bytes()).hexdigest()}"
        for archivo in sorted(codigo.glob("*.py"))
    ]
    huella_codigo = hashlib.sha256("\n".join(piezas).encode("utf-8")).hexdigest()
    return {
        "version_reporte": 1,
        "sha256_codigo_analisis": huella_codigo,
        "tipo_resultado": "ANALISIS_DE_CADENA_Y_CAPTURAS",
        "captura_actual": {
            "metadatos": analisis.actual.metadatos,
            "sha256_metadatos": analisis.actual.sha256_metadatos,
            "sha256_csv": analisis.actual.sha256_csv,
            "filas": analisis.actual.total_filas,
            "validos": len(analisis.actual.contratos),
            "rechazados": len(analisis.actual.rechazos),
        },
        "captura_anterior": None if analisis.anterior is None else {
            "metadatos": analisis.anterior.metadatos,
            "sha256_metadatos": analisis.anterior.sha256_metadatos,
            "sha256_csv": analisis.anterior.sha256_csv,
        },
        "supuestos": analisis.supuestos,
        "griegas": analisis.griegas,
        "omitidos_griegas": analisis.omitidos,
        "agregados_strike": analisis.por_strike,
        "agregados_vencimiento": analisis.por_vencimiento,
        "actividad": analisis.actividad,
        "actividad_por_strike": analisis.actividad_por_strike,
        "actividad_por_vencimiento": analisis.actividad_por_vencimiento,
        "escenario_dealer_strike": analisis.escenario_strike,
        "escenario_dealer_vencimiento": analisis.escenario_vencimiento,
        "advertencias": [
            "OI pondera una hipótesis de contratos largos; no identifica titulares ni posiciones dealer.",
            "El volumen incremental se estima entre capturas; no son operaciones individuales.",
            "La prima mid estimativa no es precio de ejecución observado.",
            "La frecuencia y frescura de actualización del open interest no están verificadas.",
            "Black-Scholes-Merton europeo aproxima opciones americanas.",
            "Las horas de cotización ausentes impiden verificar frescura bid/ask.",
        ],
    }


def ejecutar_y_guardar(
    entrada_actual: EntradaCaptura,
    supuestos: SupuestosGriegas,
    raiz_resultados: Path,
    *,
    entrada_anterior: EntradaCaptura | None = None,
    incluir_escenario_dealer: bool = False,
) -> EjecucionGuardada:
    """Guarda entradas y salidas en una carpeta nueva, sin sobrescribir análisis previos."""
    actual = validar_captura_bytes(
        entrada_actual.metadatos_json, entrada_actual.contratos_csv
    )
    anterior = (
        validar_captura_bytes(
            entrada_anterior.metadatos_json, entrada_anterior.contratos_csv
        ) if entrada_anterior is not None else None
    )
    analisis = analizar(
        actual, supuestos, anterior=anterior,
        incluir_escenario_dealer=incluir_escenario_dealer,
    )
    informe = _json_bytes(_contenido_analisis(analisis))
    huella = hashlib.sha256(informe).hexdigest()
    archivos: dict[str, bytes] = {
        "actual_metadatos.json": entrada_actual.metadatos_json,
        "actual_contratos.csv": entrada_actual.contratos_csv,
        "informe.json": informe,
        "griegas.csv": _csv_dataclasses(analisis.griegas, ResultadoGriegas),
        "omitidos_griegas.csv": _csv_dataclasses(analisis.omitidos, OmitidoGriegas),
        "agregados_strike.csv": _csv_dataclasses(analisis.por_strike, AgregadoGriegas),
        "agregados_vencimiento.csv": _csv_dataclasses(
            analisis.por_vencimiento, AgregadoGriegas
        ),
        "rechazos_actual.csv": _csv_rechazos(actual.rechazos),
    }
    if entrada_actual.proveedor_original_json is not None:
        archivos["actual_proveedor_original.json"] = entrada_actual.proveedor_original_json
    if entrada_anterior is not None:
        archivos["anterior_metadatos.json"] = entrada_anterior.metadatos_json
        archivos["anterior_contratos.csv"] = entrada_anterior.contratos_csv
        if entrada_anterior.proveedor_original_json is not None:
            archivos["anterior_proveedor_original.json"] = entrada_anterior.proveedor_original_json
    if analisis.actividad is not None:
        archivos["actividad.csv"] = _csv_dataclasses(
            analisis.actividad.contratos, ActividadContrato
        )
        archivos["actividad_strike.csv"] = _csv_dataclasses(
            analisis.actividad_por_strike, ActividadAgregada
        )
        archivos["actividad_vencimiento.csv"] = _csv_dataclasses(
            analisis.actividad_por_vencimiento, ActividadAgregada
        )
    if analisis.escenario_strike is not None:
        archivos["escenario_dealer_strike.csv"] = _csv_dataclasses(
            analisis.escenario_strike, EscenarioDealer
        )
        archivos["escenario_dealer_vencimiento.csv"] = _csv_dataclasses(
            analisis.escenario_vencimiento, EscenarioDealer
        )

    raiz_resultados = raiz_resultados.resolve()
    raiz_resultados.mkdir(parents=True, exist_ok=True)
    instante = datetime.now(timezone.utc)
    id_ejecucion = f"{instante:%Y%m%dT%H%M%S%fZ}_{uuid.uuid4().hex[:8]}"
    destino = raiz_resultados / id_ejecucion
    temporal = Path(tempfile.mkdtemp(prefix=f".{id_ejecucion}_", dir=raiz_resultados))
    try:
        for nombre, contenido in archivos.items():
            (temporal / nombre).write_bytes(contenido)
        manifiesto = {
            "id_ejecucion": id_ejecucion,
            "creado_en_utc": instante.isoformat(),
            "version_python": sys.version.split()[0],
            "huella_analisis": huella,
            "archivos_sha256": {
                nombre: hashlib.sha256(contenido).hexdigest()
                for nombre, contenido in sorted(archivos.items())
            },
        }
        (temporal / "manifiesto.json").write_bytes(_json_bytes(manifiesto))
        if destino.exists():
            raise FileExistsError(destino)
        temporal.rename(destino)
    except Exception:
        if temporal.exists() and temporal.resolve().is_relative_to(raiz_resultados):
            shutil.rmtree(temporal)
        raise
    return EjecucionGuardada(destino, huella, analisis)
