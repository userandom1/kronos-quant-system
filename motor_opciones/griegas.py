from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt
from typing import Literal


TipoOpcion = Literal["call", "put"]


# =============================================================================
# PARÁMETROS
# =============================================================================


@dataclass(frozen=True)
class ParametrosOpcion:
    """Parámetros necesarios para Black-Scholes-Merton."""

    spot: float
    strike: float
    tiempo: float
    volatilidad: float
    tipo_interes: float = 0.0
    dividendo: float = 0.0
    tipo: TipoOpcion = "call"

    def validar(self) -> None:
        """Valida los parámetros de entrada."""

        if self.spot <= 0:
            raise ValueError(
                "El precio spot debe ser mayor que cero."
            )

        if self.strike <= 0:
            raise ValueError(
                "El strike debe ser mayor que cero."
            )

        if self.tiempo <= 0:
            raise ValueError(
                "El tiempo a vencimiento debe ser mayor que cero."
            )

        if self.volatilidad <= 0:
            raise ValueError(
                "La volatilidad debe ser mayor que cero."
            )

        if self.tipo not in {
            "call",
            "put",
        }:
            raise ValueError(
                "El tipo debe ser 'call' o 'put'."
            )


# =============================================================================
# DISTRIBUCIÓN NORMAL
# =============================================================================


def normal_pdf(x: float) -> float:
    """Densidad de la distribución normal estándar."""

    return (
        exp(-0.5 * x * x)
        / sqrt(2.0 * pi)
    )


def normal_cdf(x: float) -> float:
    """Distribución acumulada normal estándar."""

    return 0.5 * (
        1.0
        + erf(
            x / sqrt(2.0)
        )
    )


# =============================================================================
# D1 Y D2
# =============================================================================


def calcular_d1(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula d1 del modelo Black-Scholes-Merton."""

    parametros.validar()

    numerador = (
        log(
            parametros.spot
            / parametros.strike
        )
        + (
            parametros.tipo_interes
            - parametros.dividendo
            + 0.5
            * parametros.volatilidad**2
        )
        * parametros.tiempo
    )

    denominador = (
        parametros.volatilidad
        * sqrt(
            parametros.tiempo
        )
    )

    return numerador / denominador


def calcular_d2(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula d2 del modelo Black-Scholes-Merton."""

    d1 = calcular_d1(
        parametros
    )

    return (
        d1
        - parametros.volatilidad
        * sqrt(
            parametros.tiempo
        )
    )


# =============================================================================
# PRECIO BLACK-SCHOLES-MERTON
# =============================================================================


def precio_opcion(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula el valor teórico de una opción europea."""

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    d2 = calcular_d2(
        parametros
    )

    descuento_dividendo = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    descuento_interes = exp(
        -parametros.tipo_interes
        * parametros.tiempo
    )

    if parametros.tipo == "call":
        return (
            parametros.spot
            * descuento_dividendo
            * normal_cdf(d1)
            - parametros.strike
            * descuento_interes
            * normal_cdf(d2)
        )

    return (
        parametros.strike
        * descuento_interes
        * normal_cdf(-d2)
        - parametros.spot
        * descuento_dividendo
        * normal_cdf(-d1)
    )


# =============================================================================
# DELTA
# =============================================================================


def delta(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula Delta."""

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    descuento = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    if parametros.tipo == "call":
        return (
            descuento
            * normal_cdf(d1)
        )

    return (
        descuento
        * (
            normal_cdf(d1)
            - 1.0
        )
    )


# =============================================================================
# GAMMA
# =============================================================================


def gamma(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula Gamma."""

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    descuento = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    return (
        descuento
        * normal_pdf(d1)
        / (
            parametros.spot
            * parametros.volatilidad
            * sqrt(
                parametros.tiempo
            )
        )
    )


# =============================================================================
# VEGA
# =============================================================================


def vega(
    parametros: ParametrosOpcion,
) -> float:
    """
    Calcula Vega por una variación absoluta de volatilidad de 1.0.

    Para obtener Vega por un punto porcentual de IV,
    utilizar vega_por_punto().
    """

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    descuento = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    return (
        parametros.spot
        * descuento
        * normal_pdf(d1)
        * sqrt(
            parametros.tiempo
        )
    )


def vega_por_punto(
    parametros: ParametrosOpcion,
) -> float:
    """Vega correspondiente a un movimiento de 1 punto de IV."""

    return (
        vega(parametros)
        / 100.0
    )


# =============================================================================
# THETA
# =============================================================================


def theta(
    parametros: ParametrosOpcion,
) -> float:
    """
    Calcula Theta anual.

    Theta representa dV/dt, donde t es tiempo de calendario.
    """

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    d2 = calcular_d2(
        parametros
    )

    descuento_dividendo = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    descuento_interes = exp(
        -parametros.tipo_interes
        * parametros.tiempo
    )

    termino_tiempo = -(
        parametros.spot
        * descuento_dividendo
        * normal_pdf(d1)
        * parametros.volatilidad
        / (
            2.0
            * sqrt(
                parametros.tiempo
            )
        )
    )

    if parametros.tipo == "call":
        return (
            termino_tiempo
            - parametros.tipo_interes
            * parametros.strike
            * descuento_interes
            * normal_cdf(d2)
            + parametros.dividendo
            * parametros.spot
            * descuento_dividendo
            * normal_cdf(d1)
        )

    return (
        termino_tiempo
        + parametros.tipo_interes
        * parametros.strike
        * descuento_interes
        * normal_cdf(-d2)
        - parametros.dividendo
        * parametros.spot
        * descuento_dividendo
        * normal_cdf(-d1)
    )


def theta_por_dia(
    parametros: ParametrosOpcion,
) -> float:
    """Convierte Theta anual a Theta aproximado por día natural."""

    return (
        theta(parametros)
        / 365.0
    )


# =============================================================================
# VANNA
# =============================================================================


def vanna(
    parametros: ParametrosOpcion,
) -> float:
    """
    Calcula Vanna.

    Vanna = dDelta/dVolatilidad
          = dVega/dSpot
    """

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    d2 = calcular_d2(
        parametros
    )

    descuento = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    return (
        -descuento
        * normal_pdf(d1)
        * d2
        / parametros.volatilidad
    )


def vanna_por_punto(
    parametros: ParametrosOpcion,
) -> float:
    """
    Cambio aproximado de Delta por un punto porcentual de IV.
    """

    return (
        vanna(parametros)
        / 100.0
    )


# =============================================================================
# CHARM / DELTA DECAY
# =============================================================================


def derivada_d1_tiempo(
    parametros: ParametrosOpcion,
) -> float:
    """Calcula la derivada de d1 respecto a T."""

    parametros.validar()

    d2 = calcular_d2(
        parametros
    )

    numerador = (
        2.0
        * (
            parametros.tipo_interes
            - parametros.dividendo
        )
        * parametros.tiempo
        - d2
        * parametros.volatilidad
        * sqrt(
            parametros.tiempo
        )
    )

    denominador = (
        2.0
        * parametros.tiempo
        * parametros.volatilidad
        * sqrt(
            parametros.tiempo
        )
    )

    return (
        numerador
        / denominador
    )


def charm_respecto_vencimiento(
    parametros: ParametrosOpcion,
) -> float:
    """
    Calcula dDelta/dT.

    T representa tiempo restante hasta vencimiento.
    """

    parametros.validar()

    d1 = calcular_d1(
        parametros
    )

    descuento = exp(
        -parametros.dividendo
        * parametros.tiempo
    )

    return (
        -parametros.dividendo
        * delta(parametros)
        + descuento
        * normal_pdf(d1)
        * derivada_d1_tiempo(
            parametros
        )
    )


def delta_decay(
    parametros: ParametrosOpcion,
) -> float:
    """
    Calcula el cambio de Delta conforme avanza el tiempo.

    Delta Decay = dDelta/dt = -dDelta/dT.
    """

    return -charm_respecto_vencimiento(
        parametros
    )


def delta_decay_por_dia(
    parametros: ParametrosOpcion,
) -> float:
    """Delta Decay aproximado por día natural."""

    return (
        delta_decay(parametros)
        / 365.0
    )


# =============================================================================
# RESUMEN
# =============================================================================


def calcular_griegas(
    parametros: ParametrosOpcion,
) -> dict[str, float]:
    """Calcula todas las métricas principales."""

    return {
        "precio": precio_opcion(
            parametros
        ),
        "delta": delta(
            parametros
        ),
        "gamma": gamma(
            parametros
        ),
        "theta_anual": theta(
            parametros
        ),
        "theta_diario": theta_por_dia(
            parametros
        ),
        "vega": vega(
            parametros
        ),
        "vega_por_punto": vega_por_punto(
            parametros
        ),
        "vanna": vanna(
            parametros
        ),
        "vanna_por_punto": vanna_por_punto(
            parametros
        ),
        "delta_decay_anual": delta_decay(
            parametros
        ),
        "delta_decay_diario": delta_decay_por_dia(
            parametros
        ),
    }