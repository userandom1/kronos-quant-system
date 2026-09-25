from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ComponenteRegimen:
    """Representa un componente individual del régimen de mercado."""

    nombre: str
    estado: str
    puntuacion: float
    peso: float

    @property
    def contribucion(self) -> float:
        """Calcula la contribución ponderada al régimen."""

        return self.puntuacion * self.peso


def limitar_puntuacion(
    valor: float,
) -> float:
    """Limita una puntuación al intervalo [-1, 1]."""

    return float(
        np.clip(
            valor,
            -1.0,
            1.0,
        )
    )


def componente_tendencia(
    precio: float,
    ma20: float,
    ma50: float,
    ma200: float,
    peso: float = 0.35,
) -> ComponenteRegimen:
    """Evalúa la estructura de tendencia."""

    if (
        precio > ma20
        and ma20 > ma50
        and ma50 > ma200
    ):
        estado = "ALCISTA_FUERTE"
        puntuacion = 1.0

    elif (
        precio > ma50
        and precio > ma200
    ):
        estado = "ALCISTA"
        puntuacion = 0.6

    elif (
        precio < ma20
        and ma20 < ma50
        and ma50 < ma200
    ):
        estado = "BAJISTA_FUERTE"
        puntuacion = -1.0

    elif (
        precio < ma50
        and precio < ma200
    ):
        estado = "BAJISTA"
        puntuacion = -0.6

    else:
        estado = "MIXTO"
        puntuacion = 0.0

    return ComponenteRegimen(
        nombre="tendencia",
        estado=estado,
        puntuacion=puntuacion,
        peso=peso,
    )


def componente_momentum(
    retorno_20d: float,
    retorno_60d: float,
    peso: float = 0.25,
) -> ComponenteRegimen:
    """Evalúa momentum de corto y medio plazo."""

    if not (
        np.isfinite(retorno_20d)
        and np.isfinite(retorno_60d)
    ):
        return ComponenteRegimen(
            nombre="momentum",
            estado="DESCONOCIDO",
            puntuacion=0.0,
            peso=peso,
        )

    puntuacion_20 = limitar_puntuacion(
        retorno_20d / 0.10
    )

    puntuacion_60 = limitar_puntuacion(
        retorno_60d / 0.20
    )

    puntuacion = (
        0.40 * puntuacion_20
        + 0.60 * puntuacion_60
    )

    if puntuacion >= 0.50:
        estado = "POSITIVO_FUERTE"

    elif puntuacion > 0.10:
        estado = "POSITIVO"

    elif puntuacion <= -0.50:
        estado = "NEGATIVO_FUERTE"

    elif puntuacion < -0.10:
        estado = "NEGATIVO"

    else:
        estado = "NEUTRAL"

    return ComponenteRegimen(
        nombre="momentum",
        estado=estado,
        puntuacion=limitar_puntuacion(
            puntuacion
        ),
        peso=peso,
    )


def componente_volatilidad(
    vol20: float,
    vol60: float,
    peso: float = 0.20,
) -> ComponenteRegimen:
    """
    Evalúa el régimen de volatilidad.

    La expansión de volatilidad penaliza el régimen y
    la contracción moderada aporta una puntuación positiva.
    """

    if not (
        np.isfinite(vol20)
        and np.isfinite(vol60)
        and vol60 > 0
    ):
        return ComponenteRegimen(
            nombre="volatilidad",
            estado="DESCONOCIDO",
            puntuacion=0.0,
            peso=peso,
        )

    ratio = vol20 / vol60

    if ratio >= 1.50:
        estado = "EXPANSION_FUERTE"
        puntuacion = -1.0

    elif ratio >= 1.20:
        estado = "EXPANSION"
        puntuacion = -0.6

    elif ratio <= 0.70:
        estado = "CONTRACCION_FUERTE"
        puntuacion = 0.7

    elif ratio <= 0.85:
        estado = "CONTRACCION"
        puntuacion = 0.4

    else:
        estado = "NORMAL"
        puntuacion = 0.0

    return ComponenteRegimen(
        nombre="volatilidad",
        estado=estado,
        puntuacion=puntuacion,
        peso=peso,
    )


def componente_drawdown(
    drawdown_actual: float,
    peso: float = 0.20,
) -> ComponenteRegimen:
    """Evalúa el deterioro del activo respecto a máximos."""

    if not np.isfinite(
        drawdown_actual
    ):
        return ComponenteRegimen(
            nombre="drawdown",
            estado="DESCONOCIDO",
            puntuacion=0.0,
            peso=peso,
        )

    if drawdown_actual >= -0.03:
        estado = "CERCA_MAXIMOS"
        puntuacion = 0.8

    elif drawdown_actual >= -0.08:
        estado = "NORMAL"
        puntuacion = 0.3

    elif drawdown_actual >= -0.15:
        estado = "CORRECCION"
        puntuacion = -0.4

    elif drawdown_actual >= -0.25:
        estado = "DETERIORO"
        puntuacion = -0.7

    else:
        estado = "DRAWDOWN_SEVERO"
        puntuacion = -1.0

    return ComponenteRegimen(
        nombre="drawdown",
        estado=estado,
        puntuacion=puntuacion,
        peso=peso,
    )


def construir_componentes(
    resultado: dict[str, object],
) -> list[ComponenteRegimen]:
    """Construye todos los componentes del régimen."""

    return [
        componente_tendencia(
            precio=float(
                resultado["precio"]
            ),
            ma20=float(
                resultado["ma20"]
            ),
            ma50=float(
                resultado["ma50"]
            ),
            ma200=float(
                resultado["ma200"]
            ),
        ),
        componente_momentum(
            retorno_20d=float(
                resultado["retorno_20d"]
            ),
            retorno_60d=float(
                resultado["retorno_60d"]
            ),
        ),
        componente_volatilidad(
            vol20=float(
                resultado["vol20"]
            ),
            vol60=float(
                resultado["vol60"]
            ),
        ),
        componente_drawdown(
            drawdown_actual=float(
                resultado[
                    "drawdown_actual"
                ]
            ),
        ),
    ]