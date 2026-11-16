"""Pruebas del contrato de capturas sin acceso a red."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from options_flow import cargar_captura


RAIZ = Path(__file__).resolve().parents[1]
EJEMPLOS = RAIZ / "ejemplos"


class ContratoCapturasTest(unittest.TestCase):
    def test_ejemplo_conserva_rechazos_y_ausencias(self) -> None:
        captura = cargar_captura(
            EJEMPLOS / "captura_sintetica.json",
            EJEMPLOS / "contratos_sinteticos.csv",
        )
        self.assertEqual(captura.total_filas, 3)
        self.assertEqual(len(captura.contratos), 2)
        self.assertEqual(captura.rechazos[0].motivos, ("mercado_cruzado",))
        self.assertEqual(captura.rechazos[0].linea_csv, 4)
        self.assertIsNone(captura.contratos[1].cotizacion_utc)
        self.assertEqual(
            captura.contratos[1].impedimento_griegas(
                captura.metadatos.capturado_en_utc, captura.metadatos.zona_mercado
            ),
            "hora_expiracion_desconocida",
        )
        self.assertEqual(len(captura.sha256_csv), 64)

    def test_duplicado_y_datos_ausentes_no_se_convierten_en_cero(self) -> None:
        with self._archivos_temporales() as (metadatos, contratos):
            filas = self._filas_ejemplo()
            filas[0]["volumen"] = ""
            filas[1] = dict(filas[0], id_contrato="OTRO-ID")
            self._escribir_csv(contratos, filas[:2])
            captura = cargar_captura(metadatos, contratos)
        self.assertEqual(len(captura.contratos), 1)
        self.assertIsNone(captura.contratos[0].volumen)
        self.assertIn("id_proveedor_duplicado", captura.rechazos[0].motivos)
        self.assertIn("contrato_duplicado", captura.rechazos[0].motivos)

    def test_multiples_motivos_y_hora_utc_obligatoria(self) -> None:
        with self._archivos_temporales() as (metadatos, contratos):
            filas = self._filas_ejemplo()
            filas[0].update(bid="8", ask="7", iv="", cotizacion_utc="2026-11-16T16:00:00+00:00")
            self._escribir_csv(contratos, filas[:1])
            captura = cargar_captura(metadatos, contratos)
            self.assertEqual(len(captura.contratos), 0)
            self.assertEqual(set(captura.rechazos[0].motivos), {"iv_invalido", "mercado_cruzado"})
            datos = json.loads(metadatos.read_text(encoding="utf-8"))
            datos["capturado_en_utc"] = "2026-11-16T15:00:00"
            metadatos.write_text(json.dumps(datos), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "capturado_en_utc_no_utc"):
                cargar_captura(metadatos, contratos)

    def test_vencimiento_se_comprueba_en_zona_de_mercado(self) -> None:
        with self._archivos_temporales() as (metadatos, contratos):
            datos = json.loads(metadatos.read_text(encoding="utf-8"))
            datos["capturado_en_utc"] = "2026-11-21T00:30:00+00:00"
            datos["spot_observado_en_utc"] = "2026-11-21T00:29:00+00:00"
            metadatos.write_text(json.dumps(datos), encoding="utf-8")
            fila = self._filas_ejemplo()[0]
            fila["expiracion_utc"] = "2026-11-21T01:00:00+00:00"
            fila["cotizacion_utc"] = "2026-11-21T00:29:00+00:00"
            self._escribir_csv(contratos, [fila])
            captura = cargar_captura(metadatos, contratos)
        self.assertEqual(len(captura.contratos), 1)
        self.assertIsNone(
            captura.contratos[0].impedimento_griegas(
                captura.metadatos.capturado_en_utc, captura.metadatos.zona_mercado
            )
        )

    def test_cabeceras_duplicadas_se_rechazan(self) -> None:
        with self._archivos_temporales() as (metadatos, contratos):
            original = (EJEMPLOS / "contratos_sinteticos.csv").read_text(encoding="utf-8")
            cabecera, resto = original.split("\n", 1)
            contratos.write_text(f"{cabecera},bid\n{resto}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "columnas_duplicadas"):
                cargar_captura(metadatos, contratos)

    def _filas_ejemplo(self) -> list[dict[str, str]]:
        with (EJEMPLOS / "contratos_sinteticos.csv").open(newline="", encoding="utf-8") as archivo:
            return list(csv.DictReader(archivo))

    def _archivos_temporales(self):
        cache = RAIZ / ".cache"
        cache.mkdir(exist_ok=True)
        temporal = tempfile.TemporaryDirectory(dir=cache)
        ruta = Path(temporal.name)
        metadatos = ruta / "metadatos.json"
        contratos = ruta / "contratos.csv"
        metadatos.write_bytes((EJEMPLOS / "captura_sintetica.json").read_bytes())

        class Contexto:
            def __enter__(self):
                return metadatos, contratos

            def __exit__(self, *args):
                temporal.cleanup()

        return Contexto()

    def _escribir_csv(self, ruta: Path, filas: list[dict[str, str]]) -> None:
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=filas[0])
            escritor.writeheader()
            escritor.writerows(filas)


if __name__ == "__main__":
    unittest.main()
