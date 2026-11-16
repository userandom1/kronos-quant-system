"""Reconciliación de agregados por strike y vencimiento."""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from options_flow import cargar_captura
from options_flow.agregados import agregar_griegas, escenario_dealer
from options_flow.griegas import SupuestosGriegas, calcular_griegas_captura


EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"


class AgregadosTest(unittest.TestCase):
    def test_strikes_reconcilian_con_vencimiento_sin_signo_dealer(self) -> None:
        captura = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        base = captura.contratos[0]
        put = replace(
            base, id_contrato="PUT-590", id_proveedor="P-590", tipo="PUT",
            strike=base.strike - 10, open_interest=50,
        )
        sin_oi = replace(
            base, id_contrato="CALL-610", id_proveedor="C-610",
            strike=base.strike + 10, open_interest=None,
        )
        captura = replace(captura, contratos=(base, put, sin_oi))
        griegas, omitidos = calcular_griegas_captura(
            captura, SupuestosGriegas(0.04, 0.01)
        )
        self.assertFalse(omitidos)
        strikes = agregar_griegas(captura, griegas, por_strike=True)
        vencimientos = agregar_griegas(captura, griegas, por_strike=False)
        self.assertEqual(len(strikes), 3)
        self.assertEqual(len(vencimientos), 2)
        call = next(f for f in vencimientos if f.tipo == "CALL")
        put_agregado = next(f for f in vencimientos if f.tipo == "PUT")
        self.assertEqual((call.contratos_con_griegas, call.contratos_con_oi), (2, 1))
        self.assertEqual(call.oi_conocido, 540)
        self.assertAlmostEqual(call.delta_oi_unidades, griegas[0].delta * 540 * 100)
        self.assertAlmostEqual(
            call.delta_oi_unidades,
            sum(f.delta_oi_unidades or 0 for f in strikes if f.tipo == "CALL"),
        )
        self.assertLess(put_agregado.delta_oi_unidades, 0)
        self.assertEqual(call.supuesto, "CADA_CONTRATO_ABIERTO_LARGO")
        fila_sin_oi = next(f for f in strikes if f.strike == 610)
        self.assertIsNone(fila_sin_oi.delta_oi_unidades)
        escenario = escenario_dealer(vencimientos)
        self.assertEqual(len(escenario), 1)
        self.assertAlmostEqual(
            escenario[0].gamma_oi_unidades_por_precio,
            -call.gamma_oi_unidades_por_precio + put_agregado.gamma_oi_unidades_por_precio,
        )
        self.assertEqual(
            escenario[0].convencion, "HIPOTESIS_CALLS_CORTAS_PUTS_LARGAS"
        )

    def test_griegas_de_otra_captura_se_rechazan(self) -> None:
        captura = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        griegas, _ = calcular_griegas_captura(captura, SupuestosGriegas(0.04, 0.01))
        ajena = (replace(griegas[0], id_captura="OTRA"),)
        with self.assertRaisesRegex(ValueError, "no_corresponden_a_captura"):
            agregar_griegas(captura, ajena, por_strike=True)


if __name__ == "__main__":
    unittest.main()
