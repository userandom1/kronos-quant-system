from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ResultadoMotor:
    """Resultado normalizado de un motor del sistema."""

    nombre: str
    estado: str
    datos: dict[str, object] = field(
        default_factory=dict
    )
    error: str | None = None


@dataclass(slots=True)
class ResultadoActivo:
    """Resultado agregado del análisis de un activo."""

    simbolo: str
    clase: str
    timestamp: datetime

    motores: dict[
        str,
        ResultadoMotor,
    ] = field(
        default_factory=dict
    )

    def agregar(
        self,
        resultado: ResultadoMotor,
    ) -> None:
        """Añade un resultado al activo."""

        self.motores[
            resultado.nombre
        ] = resultado

    def resumen_estados(
        self,
    ) -> dict[str, str]:
        """Devuelve el estado de todos los motores."""

        return {
            nombre: resultado.estado
            for nombre, resultado
            in self.motores.items()
        }