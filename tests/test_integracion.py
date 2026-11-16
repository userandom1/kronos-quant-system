"""Validación del comprobador de ejecuciones persistidas."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from options_flow.ejecucion import EntradaCaptura, ejecutar_y_guardar
from options_flow.griegas import SupuestosGriegas
from scripts.verificar_ejecucion import verificar


RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "ejemplos"


class IntegracionTest(unittest.TestCase):
    def test_ejecucion_completa_y_manipulacion_detectada(self) -> None:
        actual = EntradaCaptura.desde_archivos(
            EJEMPLOS / "captura_sintetica_2.json",
            EJEMPLOS / "contratos_sinteticos_2.csv",
        )
        anterior = EntradaCaptura.desde_archivos(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        cache = RAIZ / ".cache"
        cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporal:
            ejecucion = ejecutar_y_guardar(
                actual, SupuestosGriegas(0.04, 0.01), Path(temporal),
                entrada_anterior=anterior, incluir_escenario_dealer=True,
            )
            resultado = verificar(ejecucion.ruta)
            self.assertEqual(resultado["estado"], "OK")
            self.assertGreater(resultado["contratos_comparables"], 0)
            archivo = ejecucion.ruta / "agregados_strike.csv"
            archivo.write_bytes(archivo.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "huella incorrecta"):
                verificar(ejecucion.ruta)


if __name__ == "__main__":
    unittest.main()
