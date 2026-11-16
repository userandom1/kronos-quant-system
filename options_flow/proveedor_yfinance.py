"""Captura en vivo de cadenas Yahoo mediante yfinance, con procedencia explícita."""

from __future__ import annotations

import csv
import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .capturas import COLUMNAS


@dataclass(frozen=True)
class CapturaEnVivo:
    metadatos_json: bytes
    contratos_csv: bytes
    proveedor_original_json: bytes
    vencimientos: tuple[str, ...]


def _numero(valor: object) -> str:
    if valor is None:
        return ""
    try:
        if not math.isfinite(float(valor)):
            return ""
    except (TypeError, ValueError, OverflowError):
        return str(valor)
    return str(valor)


def _cantidad(valor: object) -> str:
    numero = _numero(valor)
    if not numero:
        return ""
    try:
        decimal = Decimal(numero)
    except (InvalidOperation, TypeError, ValueError):
        return numero
    return str(int(decimal)) if decimal == decimal.to_integral_value() else numero


def _iso_utc(valor: object) -> str:
    if valor is None:
        return ""
    try:
        if hasattr(valor, "to_pydatetime"):
            valor = valor.to_pydatetime()
        if isinstance(valor, datetime) and valor.tzinfo is not None:
            return valor.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        pass
    return ""


def capturar_yfinance(
    simbolo: str,
    vencimientos_solicitados: tuple[str, ...] = (),
    *,
    max_vencimientos: int = 3,
    ticker_factory: Callable[[str], object] | None = None,
) -> CapturaEnVivo:
    """Descarga cadenas; no confunde la última operación con una cotización."""
    simbolo = simbolo.strip().upper()
    if not simbolo or max_vencimientos < 1:
        raise ValueError("simbolo_o_numero_de_vencimientos_invalido")
    if ticker_factory is None:
        try:
            import yfinance as yf
        except ImportError as error:
            raise RuntimeError("Falta yfinance; instala requirements-live.txt") from error
        yf.set_tz_cache_location(str(Path(__file__).resolve().parents[1] / ".cache" / "yfinance"))
        ticker_factory = yf.Ticker
    ticker = ticker_factory(simbolo)
    disponibles = tuple(ticker.options)
    if not disponibles:
        raise ValueError("sin_vencimientos_disponibles")
    if vencimientos_solicitados:
        vencimientos = tuple(dict.fromkeys(vencimientos_solicitados))
        faltantes = set(vencimientos) - set(disponibles)
        if faltantes:
            raise ValueError(f"vencimientos_no_disponibles: {sorted(faltantes)}")
    else:
        vencimientos = disponibles[:max_vencimientos]

    inicio = datetime.now(timezone.utc)
    filas: list[dict[str, str]] = []
    crudo: list[dict[str, object]] = []
    cotizaciones_subyacente: list[dict[str, object]] = []
    for vencimiento in vencimientos:
        cadena = ticker.option_chain(vencimiento)
        cotizacion = cadena.underlying or {}
        cotizaciones_subyacente.append(dict(cotizacion))
        for tipo, tabla in (("CALL", cadena.calls), ("PUT", cadena.puts)):
            if tabla is None:
                continue
            for original in tabla.to_dict(orient="records"):
                crudo.append({"vencimiento": vencimiento, "tipo": tipo, **original})
                simbolo_proveedor = str(original.get("contractSymbol") or "")
                strike = _numero(original.get("strike"))
                tamano = str(original.get("contractSize") or "")
                fila = {
                    "id_contrato": f"{simbolo}|{vencimiento}|{tipo}|{strike}",
                    "id_proveedor": simbolo_proveedor,
                    "tipo": tipo,
                    "strike": strike,
                    "vencimiento": vencimiento,
                    "expiracion_utc": "",
                    "multiplicador": "100" if tamano == "REGULAR" else "",
                    "bid": _numero(original.get("bid")),
                    "ask": _numero(original.get("ask")),
                    "iv": _numero(original.get("impliedVolatility")),
                    "volumen": _cantidad(original.get("volume")),
                    "open_interest": _cantidad(original.get("openInterest")),
                    "cotizacion_utc": "",
                    "ultimo_trade_utc": _iso_utc(original.get("lastTradeDate")),
                    "tamano_proveedor": tamano,
                    "divisa_contrato": str(original.get("currency") or ""),
                }
                filas.append(fila)
    fin = datetime.now(timezone.utc)
    if not filas:
        raise ValueError("sin_contratos_descargados")
    cotizaciones_validas = [
        c for c in cotizaciones_subyacente
        if c.get("regularMarketPrice") is not None
        and c.get("regularMarketTime") is not None
    ]
    if not cotizaciones_validas:
        raise ValueError("sin_spot_con_hora_del_proveedor")
    spot_origen = max(cotizaciones_validas, key=lambda c: c["regularMarketTime"])
    zona = spot_origen.get("exchangeTimezoneName")
    try:
        ZoneInfo(zona)
    except (TypeError, ZoneInfoNotFoundError) as error:
        raise ValueError("zona_mercado_no_verificada") from error
    hora_spot = datetime.fromtimestamp(
        spot_origen["regularMarketTime"], timezone.utc
    )
    if hora_spot > fin:
        raise ValueError("spot_posterior_a_captura")
    divisa = spot_origen.get("currency")
    if not divisa:
        raise ValueError("divisa_no_verificada")
    if not math.isfinite(float(spot_origen["regularMarketPrice"])) or float(
        spot_origen["regularMarketPrice"]
    ) <= 0:
        raise ValueError("spot_invalido")
    metadatos = {
        "version_esquema": 1,
        "id_captura": f"{simbolo}-{fin:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex[:8]}",
        "subyacente": simbolo,
        "proveedor": "YFINANCE",
        "version_proveedor": _version_yfinance(),
        "captura_iniciada_utc": inicio.isoformat(),
        "capturado_en_utc": fin.isoformat(),
        "spot": str(spot_origen["regularMarketPrice"]),
        "divisa": str(divisa).upper(),
        "fuente_spot": "YFINANCE_OPTION_UNDERLYING_QUOTE",
        "spot_observado_en_utc": hora_spot.isoformat(),
        "zona_mercado": str(zona),
        "vencimientos": list(vencimientos),
        "politica_multiplicador": "REGULAR=>100; otros rechazados",
        "hora_cotizacion": "DESCONOCIDA; lastTradeDate es hora de la última operación",
    }
    salida = StringIO(newline="")
    escritor = csv.DictWriter(
        salida, fieldnames=[*COLUMNAS, "ultimo_trade_utc", "tamano_proveedor", "divisa_contrato"],
        lineterminator="\n",
    )
    escritor.writeheader()
    escritor.writerows(filas)
    return CapturaEnVivo(
        metadatos_json=(json.dumps(metadatos, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        contratos_csv=salida.getvalue().encode("utf-8"),
        proveedor_original_json=(json.dumps(
            {"cadenas": crudo, "cotizaciones_subyacente": cotizaciones_subyacente},
            ensure_ascii=False, indent=2, default=str,
        ) + "\n").encode("utf-8"),
        vencimientos=vencimientos,
    )


def _version_yfinance() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("yfinance")
    except PackageNotFoundError:
        return "NO_DISPONIBLE"
