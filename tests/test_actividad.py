"""Actividad inferida de snapshots y sus límites."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from options_flow import cargar_captura
from options_flow.actividad import agregar_actividad, comparar_capturas


EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"


class ActividadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.anterior = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        self.actual = cargar_captura(
            EJEMPLOS / "captura_sintetica_2.json",
            EJEMPLOS / "contratos_sinteticos_2.csv",
        )

    def test_incremento_solo_con_base_y_sin_direccion_inferida(self) -> None:
        comparacion = comparar_capturas(self.anterior, self.actual)
        filas = {fila.id_contrato: fila for fila in comparacion.contratos}
        call = filas["QQQ-20261120-C600"]
        self.assertEqual(call.incremento_volumen_estimado, 10)
        self.assertEqual(call.cambio_oi_reportado, 0)
        self.assertEqual(call.cambio_iv, Decimal("0.01"))
        self.assertEqual(call.prima_mid_estimativa, Decimal("12450.00"))
        self.assertEqual(filas["QQQ-20261116-P595"].estado_volumen, "VOLUMEN_RETROCEDE")
        self.assertIsNone(filas["QQQ-20261116-P595"].incremento_volumen_estimado)
        self.assertEqual(filas["QQQ-20261120-C610"].estado_volumen, "SIN_BASE_ANTERIOR")
        self.assertEqual(comparacion.tipo_dato, "COMPARACION_DE_CAPTURAS_NO_OPERACIONES")
        self.assertFalse(hasattr(call, "direccion_orden"))
        resumen = agregar_actividad(comparacion, por_strike=False)
        calls = next(f for f in resumen if f.tipo == "CALL" and f.vencimiento == "2026-11-20")
        self.assertEqual(calls.contratos_comparables, 1)
        self.assertEqual(calls.incremento_volumen_estimado, 10)
        self.assertEqual(calls.prima_mid_estimativa, Decimal("12450.00"))

    def test_cambio_de_dia_no_resta_volumen(self) -> None:
        metadatos = replace(
            self.actual.metadatos,
            capturado_en_utc=datetime.fromisoformat("2026-11-17T15:05:00+00:00"),
        )
        actual = replace(self.actual, metadatos=metadatos)
        comparacion = comparar_capturas(self.anterior, actual)
        self.assertFalse(comparacion.misma_fecha_mercado)
        self.assertTrue(all(
            fila.incremento_volumen_estimado is None for fila in comparacion.contratos
        ))
        self.assertEqual(comparacion.contratos[0].estado_volumen, "DIA_MERCADO_DISTINTO")

    def test_fuentes_distintas_no_se_comparan(self) -> None:
        actual = replace(
            self.actual,
            metadatos=replace(self.actual.metadatos, proveedor="OTRO"),
        )
        with self.assertRaisesRegex(ValueError, "capturas_incompatibles"):
            comparar_capturas(self.anterior, actual)

    def test_orden_temporal_obligatorio(self) -> None:
        with self.assertRaisesRegex(ValueError, "capturas_fuera_de_orden"):
            comparar_capturas(self.actual, self.anterior)


if __name__ == "__main__":
    unittest.main()
