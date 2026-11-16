"""Contrato de entrada para cadenas de opciones guardadas."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


COLUMNAS = (
    "id_contrato",
    "id_proveedor",
    "tipo",
    "strike",
    "vencimiento",
    "expiracion_utc",
    "multiplicador",
    "bid",
    "ask",
    "iv",
    "volumen",
    "open_interest",
    "cotizacion_utc",
)


@dataclass(frozen=True)
class Metadatos:
    id_captura: str
    subyacente: str
    proveedor: str
    capturado_en_utc: datetime
    spot: Decimal
    divisa: str
    fuente_spot: str
    spot_observado_en_utc: datetime | None
    zona_mercado: str


@dataclass(frozen=True)
class Contrato:
    id_contrato: str
    id_proveedor: str
    tipo: str
    strike: Decimal
    vencimiento: date
    expiracion_utc: datetime | None
    multiplicador: int
    bid: Decimal
    ask: Decimal
    iv: Decimal
    volumen: int | None
    open_interest: int | None
    cotizacion_utc: datetime | None

    def impedimento_griegas(self, captura: datetime, zona_mercado: str) -> str | None:
        """Exige fecha y bloquea 0DTE sin hora exacta de expiración."""
        if self.expiracion_utc is not None:
            if self.expiracion_utc <= captura:
                return "expirado"
            return None
        if self.vencimiento <= captura.astimezone(ZoneInfo(zona_mercado)).date():
            return "hora_expiracion_desconocida"
        return None


@dataclass(frozen=True)
class Rechazo:
    linea_csv: int
    motivos: tuple[str, ...]
    fila_original: dict[str, str]


@dataclass(frozen=True)
class CapturaValidada:
    metadatos: Metadatos
    contratos: tuple[Contrato, ...]
    rechazos: tuple[Rechazo, ...]
    sha256_csv: str
    sha256_metadatos: str

    @property
    def total_filas(self) -> int:
        return len(self.contratos) + len(self.rechazos)


def _texto(valor: object, nombre: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre}_ausente")
    return valor.strip()


def _decimal(valor: object, nombre: str, *, permitir_cero: bool = False) -> Decimal:
    try:
        numero = Decimal(_texto(valor, nombre))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{nombre}_invalido") from error
    if not numero.is_finite() or numero < 0 or (numero == 0 and not permitir_cero):
        raise ValueError(f"{nombre}_invalido")
    return numero


def _entero(valor: object, nombre: str, *, opcional: bool = False) -> int | None:
    if opcional and (valor is None or valor == ""):
        return None
    texto = _texto(valor, nombre)
    if not texto.isascii() or not texto.isdecimal():
        raise ValueError(f"{nombre}_invalido")
    numero = int(texto)
    if numero < 0 or (not opcional and numero == 0):
        raise ValueError(f"{nombre}_invalido")
    return numero


def _utc(valor: object, nombre: str, *, opcional: bool = False) -> datetime | None:
    if opcional and (valor is None or valor == ""):
        return None
    try:
        instante = datetime.fromisoformat(_texto(valor, nombre))
    except ValueError as error:
        raise ValueError(f"{nombre}_invalido") from error
    if instante.tzinfo is None or instante.utcoffset() != timedelta(0):
        raise ValueError(f"{nombre}_no_utc")
    return instante


def _metadatos(datos: dict[str, object]) -> Metadatos:
    if datos.get("version_esquema") != 1:
        raise ValueError("version_esquema_incompatible")
    zona_mercado = _texto(datos.get("zona_mercado"), "zona_mercado")
    try:
        ZoneInfo(zona_mercado)
    except ZoneInfoNotFoundError as error:
        raise ValueError("zona_mercado_invalida") from error
    return Metadatos(
        id_captura=_texto(datos.get("id_captura"), "id_captura"),
        subyacente=_texto(datos.get("subyacente"), "subyacente").upper(),
        proveedor=_texto(datos.get("proveedor"), "proveedor"),
        capturado_en_utc=_utc(datos.get("capturado_en_utc"), "capturado_en_utc"),
        spot=_decimal(datos.get("spot"), "spot"),
        divisa=_texto(datos.get("divisa"), "divisa").upper(),
        fuente_spot=_texto(datos.get("fuente_spot"), "fuente_spot"),
        spot_observado_en_utc=_utc(
            datos.get("spot_observado_en_utc"), "spot_observado_en_utc", opcional=True
        ),
        zona_mercado=zona_mercado,
    )


def _contrato(fila: dict[str, str], zona_mercado: str) -> tuple[Contrato | None, tuple[str, ...]]:
    motivos: list[str] = []

    def leer(funcion, *args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except ValueError as error:
            motivos.append(str(error))
            return None

    identidad = leer(_texto, fila.get("id_contrato"), "id_contrato")
    proveedor = leer(_texto, fila.get("id_proveedor"), "id_proveedor")
    tipo = leer(_texto, fila.get("tipo"), "tipo")
    if tipo is not None:
        tipo = tipo.upper()
        if tipo not in {"CALL", "PUT"}:
            motivos.append("tipo_invalido")
    strike = leer(_decimal, fila.get("strike"), "strike")
    try:
        vencimiento = date.fromisoformat(_texto(fila.get("vencimiento"), "vencimiento"))
    except ValueError:
        vencimiento = None
        motivos.append("vencimiento_invalido")
    expiracion = leer(_utc, fila.get("expiracion_utc"), "expiracion_utc", opcional=True)
    multiplicador = leer(_entero, fila.get("multiplicador"), "multiplicador")
    bid = leer(_decimal, fila.get("bid"), "bid", permitir_cero=True)
    ask = leer(_decimal, fila.get("ask"), "ask")
    iv = leer(_decimal, fila.get("iv"), "iv")
    volumen = leer(_entero, fila.get("volumen"), "volumen", opcional=True)
    oi = leer(_entero, fila.get("open_interest"), "open_interest", opcional=True)
    cotizacion = leer(_utc, fila.get("cotizacion_utc"), "cotizacion_utc", opcional=True)
    if bid is not None and ask is not None and bid > ask:
        motivos.append("mercado_cruzado")
    if (
        expiracion is not None
        and vencimiento is not None
        and expiracion.astimezone(ZoneInfo(zona_mercado)).date() != vencimiento
    ):
        motivos.append("expiracion_no_coincide")
    if motivos:
        return None, tuple(dict.fromkeys(motivos))
    return (
        Contrato(
            identidad, proveedor, tipo, strike, vencimiento, expiracion,
            multiplicador, bid, ask, iv, volumen, oi, cotizacion,
        ),
        (),
    )


def cargar_captura(ruta_metadatos: Path, ruta_csv: Path) -> CapturaValidada:
    """Lee una captura sin modificar originales y conserva cada rechazo."""
    return validar_captura_bytes(ruta_metadatos.read_bytes(), ruta_csv.read_bytes())


def validar_captura_bytes(bytes_metadata: bytes, bytes_csv: bytes) -> CapturaValidada:
    """Valida los bytes originales; permite procesar capturas vivas sin ficheros temporales."""
    datos = json.loads(bytes_metadata.decode("utf-8-sig"))
    if not isinstance(datos, dict):
        raise ValueError("metadatos_incorrectos")
    metadatos = _metadatos(datos)
    if (
        metadatos.spot_observado_en_utc is not None
        and metadatos.spot_observado_en_utc > metadatos.capturado_en_utc
    ):
        raise ValueError("spot_posterior_a_captura")

    validos: list[Contrato] = []
    rechazados: list[Rechazo] = []
    ids: set[str] = set()
    ids_proveedor: set[str] = set()
    claves: set[tuple[date, str, Decimal]] = set()

    lector = csv.DictReader(StringIO(bytes_csv.decode("utf-8-sig"), newline=""))
    if lector.fieldnames is None or set(COLUMNAS) - set(lector.fieldnames):
        raise ValueError("columnas_obligatorias_ausentes")
    if len(lector.fieldnames) != len(set(lector.fieldnames)):
        raise ValueError("columnas_duplicadas")
    for linea, fila in enumerate(lector, start=2):
        contrato, motivos = _contrato(fila, metadatos.zona_mercado)
        razones = list(motivos)
        if None in fila:
            razones.append("columnas_extra")
        if contrato is not None:
            clave = (contrato.vencimiento, contrato.tipo, contrato.strike)
            if contrato.id_contrato in ids:
                razones.append("id_contrato_duplicado")
            if contrato.id_proveedor in ids_proveedor:
                razones.append("id_proveedor_duplicado")
            if clave in claves:
                razones.append("contrato_duplicado")
            if contrato.expiracion_utc is not None and contrato.expiracion_utc <= metadatos.capturado_en_utc:
                razones.append("expirado")
            elif contrato.vencimiento < metadatos.capturado_en_utc.astimezone(
                ZoneInfo(metadatos.zona_mercado)
            ).date():
                razones.append("expirado")
            if contrato.cotizacion_utc is not None and contrato.cotizacion_utc > metadatos.capturado_en_utc:
                razones.append("cotizacion_posterior_a_captura")
            divisa_contrato = fila.get("divisa_contrato")
            if divisa_contrato and divisa_contrato.upper() != metadatos.divisa:
                razones.append("divisa_contrato_incompatible")
        if razones:
            rechazados.append(Rechazo(linea, tuple(dict.fromkeys(razones)), dict(fila)))
        else:
            validos.append(contrato)
            ids.add(contrato.id_contrato)
            ids_proveedor.add(contrato.id_proveedor)
            claves.add(clave)
    return CapturaValidada(
        metadatos,
        tuple(validos),
        tuple(rechazados),
        hashlib.sha256(bytes_csv).hexdigest(),
        hashlib.sha256(bytes_metadata).hexdigest(),
    )
