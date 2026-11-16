"""Reproducción y persistencia inmutable del análisis."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from options_flow.ejecucion import EntradaCaptura, ejecutar_y_guardar
from options_flow.griegas import SupuestosGriegas


RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "ejemplos"


class EjecucionTest(unittest.TestCase):
    def test_dos_ejecuciones_con_mismos_datos_tienen_informe_identico(self) -> None:
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
            destino = Path(temporal)
            self.assertTrue(destino.resolve().is_relative_to(RAIZ.resolve()))
            uno = ejecutar_y_guardar(
                actual, SupuestosGriegas(0.04, 0.01), destino,
                entrada_anterior=anterior, incluir_escenario_dealer=True,
            )
            dos = ejecutar_y_guardar(
                actual, SupuestosGriegas(0.04, 0.01), destino,
                entrada_anterior=anterior, incluir_escenario_dealer=True,
            )
            self.assertNotEqual(uno.ruta, dos.ruta)
            self.assertEqual(uno.huella_analisis, dos.huella_analisis)
            self.assertEqual(
                (uno.ruta / "informe.json").read_bytes(),
                (dos.ruta / "informe.json").read_bytes(),
            )
            informe = json.loads((uno.ruta / "informe.json").read_text(encoding="utf-8"))
            self.assertEqual(len(informe["sha256_codigo_analisis"]), 64)
            self.assertEqual((uno.ruta / "actual_contratos.csv").read_bytes(), actual.contratos_csv)
            self.assertTrue((uno.ruta / "actividad.csv").exists())
            self.assertTrue((uno.ruta / "escenario_dealer_strike.csv").exists())
            manifiesto = json.loads((uno.ruta / "manifiesto.json").read_text(encoding="utf-8"))
            for nombre, huella in manifiesto["archivos_sha256"].items():
                self.assertEqual(
                    hashlib.sha256((uno.ruta / nombre).read_bytes()).hexdigest(), huella
                )

    def test_fila_con_columnas_extra_queda_en_rechazos_guardados(self) -> None:
        entrada = EntradaCaptura.desde_archivos(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        lineas = entrada.contratos_csv.decode("utf-8").splitlines()
        lineas[1] += ",EXTRA"
        entrada = EntradaCaptura(
            entrada.metadatos_json, ("\n".join(lineas) + "\n").encode("utf-8")
        )
        cache = RAIZ / ".cache"
        cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as temporal:
            self.assertTrue(Path(temporal).resolve().is_relative_to(RAIZ.resolve()))
            ejecucion = ejecutar_y_guardar(
                entrada, SupuestosGriegas(0.04, 0.01), Path(temporal)
            )
            rechazados = (ejecucion.ruta / "rechazos_actual.csv").read_text(encoding="utf-8")
            self.assertIn("columnas_extra", rechazados)
            self.assertIn("EXTRA", rechazados)
            self.assertFalse((ejecucion.ruta / "escenario_dealer_strike.csv").exists())


if __name__ == "__main__":
    unittest.main()
