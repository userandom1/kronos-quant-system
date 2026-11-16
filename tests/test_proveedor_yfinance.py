"""Adaptación de la fuente en vivo sin llamar a la red."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
from types import SimpleNamespace
import unittest

from options_flow.capturas import validar_captura_bytes
from options_flow.proveedor_yfinance import capturar_yfinance


class TablaFalsa:
    def __init__(self, filas):
        self.filas = filas

    def to_dict(self, orient):
        assert orient == "records"
        return self.filas


class TickerFalso:
    options = ("2099-12-17",)

    def __init__(self, simbolo):
        self.simbolo = simbolo

    def option_chain(self, vencimiento):
        ahora = datetime.now(timezone.utc)
        base = {
            "strike": 100.0,
            "bid": 3.0,
            "ask": 3.2,
            "impliedVolatility": 0.2,
            "volume": 4.0,
            "openInterest": 30.0,
            "currency": "USD",
            "lastTradeDate": ahora - timedelta(minutes=5),
        }
        return SimpleNamespace(
            calls=TablaFalsa([dict(base, contractSymbol="TESTC", contractSize="REGULAR")]),
            puts=TablaFalsa([dict(base, contractSymbol="TESTP", contractSize="ADJUSTED")]),
            underlying={
                "regularMarketPrice": 100.5,
                "regularMarketTime": int((ahora - timedelta(minutes=1)).timestamp()),
                "currency": "USD",
                "exchangeTimezoneName": "America/New_York",
            },
        )


class ProveedorTest(unittest.TestCase):
    def test_hora_ultima_operacion_no_se_usa_como_hora_cotizacion(self) -> None:
        vivo = capturar_yfinance("TEST", ticker_factory=TickerFalso)
        filas = list(csv.DictReader(StringIO(vivo.contratos_csv.decode("utf-8"))))
        self.assertTrue(filas[0]["ultimo_trade_utc"])
        self.assertEqual(filas[0]["cotizacion_utc"], "")
        self.assertEqual(filas[0]["multiplicador"], "100")
        self.assertEqual(filas[1]["multiplicador"], "")
        captura = validar_captura_bytes(vivo.metadatos_json, vivo.contratos_csv)
        self.assertEqual(len(captura.contratos), 1)
        self.assertIn("multiplicador_ausente", captura.rechazos[0].motivos)


if __name__ == "__main__":
    unittest.main()
