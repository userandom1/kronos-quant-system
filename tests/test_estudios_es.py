"""Escenario dealer y alineación SPX/ES."""

import unittest

from options_flow.estudios_es import calcular_estudio


class EstudioEsTest(unittest.TestCase):
    def test_gex_dex_y_nivel_es(self) -> None:
        filas = [
            {"tipo": "CALL", "strike": 5000, "open_interest": 2,
             "delta": 0.5, "gamma": 0.001, "multiplicador": 100},
            {"tipo": "PUT", "strike": 5000, "open_interest": 3,
             "delta": -0.4, "gamma": 0.002, "multiplicador": 100},
        ]
        resultado = calcular_estudio(
            filas, spx_referencia=5000, es_referencia=5012,
            spx_hora_utc="2026-11-16T20:00:00+00:00",
            es_hora_utc="2026-11-16T20:01:00+00:00",
        )
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nivel_es_proxy"], 5012)
        self.assertAlmostEqual(resultado[0]["gex_usd_por_1pct"], 100_000.0)
        self.assertAlmostEqual(resultado[0]["dex_usd"], -1_100_000.0)

    def test_rechaza_referencias_desfasadas(self) -> None:
        with self.assertRaisesRegex(ValueError, "referencias_no_sincronizadas"):
            calcular_estudio(
                [{"tipo": "CALL", "strike": 5000, "open_interest": 1,
                  "delta": 0.5, "gamma": 0.001, "multiplicador": 100}],
                spx_referencia=5000, es_referencia=5012,
                spx_hora_utc="2026-11-16T20:00:00+00:00",
                es_hora_utc="2026-11-16T20:06:00+00:00",
            )

    def test_rechaza_oi_fraccionario(self) -> None:
        with self.assertRaisesRegex(ValueError, "contrato_spx_invalido"):
            calcular_estudio(
                [{"tipo": "CALL", "strike": 5000, "open_interest": 1.5,
                  "delta": 0.5, "gamma": 0.001, "multiplicador": 100}],
                spx_referencia=5000, es_referencia=5012,
                spx_hora_utc="2026-11-16T20:00:00+00:00",
                es_hora_utc="2026-11-16T20:00:00+00:00",
            )


if __name__ == "__main__":
    unittest.main()
