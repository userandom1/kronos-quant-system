from __future__ import annotations

from dataclasses import dataclass

from motor_mercado.componentes_regimen import (
    ComponenteRegimen,
)


@dataclass(frozen=True, slots=True)
class ResultadoRegimen:
    """Resultado final del régimen de un activo."""

    estado: str
    puntuacion: float
    confianza: str


def calcular_puntuacion_regimen(
    componentes: list[ComponenteRegimen],
) -> float:
    """Calcula la puntuación ponderada total."""

    if not componentes:
        return 0.0

    peso_total = sum(
        componente.peso
        for componente in componentes
    )

    if peso_total <= 0:
        return 0.0

    puntuacion = sum(
        componente.contribucion
        for componente in componentes
    )

    return float(
        puntuacion / peso_total
    )


def clasificar_estado(
    puntuacion: float,
) -> str:
    """Clasifica el estado global del activo."""

    if puntuacion >= 0.65:
        return "RISK_ON_FUERTE"

    if puntuacion >= 0.25:
        return "RISK_ON"

    if puntuacion <= -0.65:
        return "RISK_OFF_FUERTE"

    if puntuacion <= -0.25:
        return "RISK_OFF"

    return "NEUTRAL"


def calcular_confianza(
    componentes: list[ComponenteRegimen],
) -> str:
    """Estima la coherencia entre componentes."""

    if not componentes:
        return "BAJA"

    signos = []

    for componente in componentes:
        if componente.puntuacion > 0.10:
            signos.append(1)

        elif componente.puntuacion < -0.10:
            signos.append(-1)

        else:
            signos.append(0)

    positivos = signos.count(1)
    negativos = signos.count(-1)

    dominante = max(
        positivos,
        negativos,
    )

    if dominante >= 3:
        return "ALTA"

    if dominante >= 2:
        return "MEDIA"

    return "BAJA"


def clasificar_regimen(
    componentes: list[ComponenteRegimen],
) -> ResultadoRegimen:
    """Genera el régimen final."""

    puntuacion = (
        calcular_puntuacion_regimen(
            componentes
        )
    )

    estado = clasificar_estado(
        puntuacion
    )

    confianza = calcular_confianza(
        componentes
    )

    return ResultadoRegimen(
        estado=estado,
        puntuacion=puntuacion,
        confianza=confianza,
    )