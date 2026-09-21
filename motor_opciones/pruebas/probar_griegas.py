from dataclasses import replace
from pathlib import Path
import sys
import unittest


RUTA_BASE = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(RUTA_BASE),
)


from motor_opciones.griegas import (
    ParametrosOpcion,
    calcular_griegas,
    delta,
    delta_decay,
    gamma,
    precio_opcion,
    theta,
    vanna,
    vega,
)


class PruebasGriegas(unittest.TestCase):
    """Pruebas numéricas del motor Black-Scholes-Merton."""

    def setUp(self) -> None:
        """Crea parámetros base para cada prueba."""

        self.call = ParametrosOpcion(
            spot=100.0,
            strike=100.0,
            tiempo=30.0 / 365.0,
            volatilidad=0.20,
            tipo_interes=0.04,
            dividendo=0.01,
            tipo="call",
        )

        self.put = replace(
            self.call,
            tipo="put",
        )

    def test_delta_call_put(self) -> None:
        """Comprueba la relación entre Delta call y put."""

        diferencia = (
            delta(self.call)
            - delta(self.put)
        )

        esperado = (
            2.718281828459045
            ** (
                -self.call.dividendo
                * self.call.tiempo
            )
        )

        self.assertAlmostEqual(
            diferencia,
            esperado,
            places=8,
        )

    def test_gamma_call_put(self) -> None:
        """Gamma debe coincidir para call y put."""

        self.assertAlmostEqual(
            gamma(self.call),
            gamma(self.put),
            places=12,
        )

    def test_vanna_call_put(self) -> None:
        """Vanna debe coincidir para call y put."""

        self.assertAlmostEqual(
            vanna(self.call),
            vanna(self.put),
            places=12,
        )

    def test_delta_diferencia_finita(self) -> None:
        """Valida Delta mediante diferencias finitas del precio."""

        h = 0.001

        arriba = replace(
            self.call,
            spot=self.call.spot + h,
        )

        abajo = replace(
            self.call,
            spot=self.call.spot - h,
        )

        delta_numerica = (
            precio_opcion(arriba)
            - precio_opcion(abajo)
        ) / (
            2.0 * h
        )

        self.assertAlmostEqual(
            delta(self.call),
            delta_numerica,
            places=5,
        )

    def test_gamma_diferencia_finita(self) -> None:
        """Valida Gamma derivando Delta respecto al spot."""

        h = 0.001

        arriba = replace(
            self.call,
            spot=self.call.spot + h,
        )

        abajo = replace(
            self.call,
            spot=self.call.spot - h,
        )

        gamma_numerica = (
            delta(arriba)
            - delta(abajo)
        ) / (
            2.0 * h
        )

        self.assertAlmostEqual(
            gamma(self.call),
            gamma_numerica,
            places=5,
        )

    def test_vega_diferencia_finita(self) -> None:
        """Valida Vega derivando el precio respecto a IV."""

        h = 0.00001

        arriba = replace(
            self.call,
            volatilidad=(
                self.call.volatilidad + h
            ),
        )

        abajo = replace(
            self.call,
            volatilidad=(
                self.call.volatilidad - h
            ),
        )

        vega_numerica = (
            precio_opcion(arriba)
            - precio_opcion(abajo)
        ) / (
            2.0 * h
        )

        self.assertAlmostEqual(
            vega(self.call),
            vega_numerica,
            places=4,
        )

    def test_vanna_diferencia_finita(self) -> None:
        """Valida Vanna derivando Delta respecto a IV."""

        h = 0.00001

        arriba = replace(
            self.call,
            volatilidad=(
                self.call.volatilidad + h
            ),
        )

        abajo = replace(
            self.call,
            volatilidad=(
                self.call.volatilidad - h
            ),
        )

        vanna_numerica = (
            delta(arriba)
            - delta(abajo)
        ) / (
            2.0 * h
        )

        self.assertAlmostEqual(
            vanna(self.call),
            vanna_numerica,
            places=4,
        )

    def test_theta_diferencia_finita(self) -> None:
        """Valida Theta como menos la derivada respecto a T."""

        h = 0.00001

        mas_tiempo = replace(
            self.call,
            tiempo=self.call.tiempo + h,
        )

        menos_tiempo = replace(
            self.call,
            tiempo=self.call.tiempo - h,
        )

        derivada_t = (
            precio_opcion(mas_tiempo)
            - precio_opcion(menos_tiempo)
        ) / (
            2.0 * h
        )

        theta_numerica = -derivada_t

        self.assertAlmostEqual(
            theta(self.call),
            theta_numerica,
            places=4,
        )

    def test_delta_decay_diferencia_finita(self) -> None:
        """Valida Delta Decay como menos dDelta/dT."""

        h = 0.00001

        mas_tiempo = replace(
            self.call,
            tiempo=self.call.tiempo + h,
        )

        menos_tiempo = replace(
            self.call,
            tiempo=self.call.tiempo - h,
        )

        derivada_delta_t = (
            delta(mas_tiempo)
            - delta(menos_tiempo)
        ) / (
            2.0 * h
        )

        delta_decay_numerico = (
            -derivada_delta_t
        )

        self.assertAlmostEqual(
            delta_decay(self.call),
            delta_decay_numerico,
            places=4,
        )

    def test_resumen_completo(self) -> None:
        """Comprueba que el resumen contiene todas las salidas."""

        resultado = calcular_griegas(
            self.call
        )

        claves = {
            "precio",
            "delta",
            "gamma",
            "theta_anual",
            "theta_diario",
            "vega",
            "vega_por_punto",
            "vanna",
            "vanna_por_punto",
            "delta_decay_anual",
            "delta_decay_diario",
        }

        self.assertEqual(
            set(resultado),
            claves,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )