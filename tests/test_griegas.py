"""Contrastes de Delta/Gamma y política de vencimiento."""

from __future__ import annotations

import math
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from options_flow import cargar_captura
from options_flow.griegas import (
    SupuestosGriegas,
    calcular_griegas_captura,
    delta_gamma,
    tiempo_hasta_vencimiento,
)


EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"


class GriegasTest(unittest.TestCase):
    def test_valores_referencia_atm_un_ano(self) -> None:
        parametros = dict(
            spot=100.0, strike=100.0, volatilidad=0.2, tiempo_anos=1.0,
            tasa_anual=0.0, dividendo_anual=0.0,
        )
        delta_call, gamma_call = delta_gamma(tipo="CALL", **parametros)
        delta_put, gamma_put = delta_gamma(tipo="PUT", **parametros)
        self.assertAlmostEqual(delta_call, 0.539827837277029, places=12)
        self.assertAlmostEqual(delta_put, -0.460172162722971, places=12)
        self.assertAlmostEqual(gamma_call, 0.0198476273738506, places=12)
        self.assertAlmostEqual(gamma_put, gamma_call, places=14)

    def test_paridad_delta_con_dividendo(self) -> None:
        parametros = dict(
            spot=101.0, strike=100.0, volatilidad=0.27, tiempo_anos=0.4,
            tasa_anual=0.04, dividendo_anual=0.03,
        )
        call, gamma_call = delta_gamma(tipo="CALL", **parametros)
        put, gamma_put = delta_gamma(tipo="PUT", **parametros)
        self.assertAlmostEqual(call - put, math.exp(-0.03 * 0.4), places=13)
        self.assertAlmostEqual(gamma_call, gamma_put, places=14)

    def test_0dte_sin_hora_se_omite_y_con_hora_se_calcula(self) -> None:
        captura = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        resultados, omitidos = calcular_griegas_captura(
            captura, SupuestosGriegas(0.04, 0.01)
        )
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].precision_tiempo, "HORA_EXACTA")
        self.assertEqual(resultados[0].id_captura, "EJEMPLO-QQQ-20261116")
        self.assertEqual(resultados[0].multiplicador, 100)
        self.assertEqual(resultados[0].volatilidad, 0.22)
        self.assertEqual(resultados[0].tasa_anual, 0.04)
        self.assertEqual(omitidos[0].motivo, "hora_expiracion_desconocida")
        contrato = replace(
            captura.contratos[1],
            expiracion_utc=datetime.fromisoformat("2026-11-16T21:00:00+00:00"),
        )
        tiempo, precision = tiempo_hasta_vencimiento(
            contrato, captura.metadatos.capturado_en_utc,
            captura.metadatos.zona_mercado,
        )
        self.assertAlmostEqual(tiempo, 6 / (365 * 24))
        self.assertEqual(precision, "HORA_EXACTA")

    def test_fecha_futura_sin_hora_usa_dias_calendario(self) -> None:
        captura = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        contrato = replace(captura.contratos[0], expiracion_utc=None)
        tiempo, precision = tiempo_hasta_vencimiento(
            contrato, captura.metadatos.capturado_en_utc,
            captura.metadatos.zona_mercado,
        )
        self.assertEqual(tiempo, 4 / 365)
        self.assertEqual(precision, "DIAS_CALENDARIO")

    def test_supuestos_invalidos_fallan(self) -> None:
        with self.assertRaisesRegex(ValueError, "deben_ser_finitos"):
            SupuestosGriegas(float("nan"), 0.0)


if __name__ == "__main__":
    unittest.main()
