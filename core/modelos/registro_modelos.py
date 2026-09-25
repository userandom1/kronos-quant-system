from __future__ import annotations

from core.modelos.modelo_base import (
    ModeloForecast,
)
from core.modelos.modelo_drift import (
    ModeloDrift,
)
from core.modelos.modelo_kronos import (
    ModeloKronos,
)
from core.modelos.modelo_momentum import (
    ModeloMomentum,
)


_MODELOS: dict[
    str,
    ModeloForecast,
] = {
    "DRIFT": ModeloDrift(),
    "MOMENTUM": ModeloMomentum(),
    "KRONOS": ModeloKronos(),
}


def registrar_modelo(
    modelo: ModeloForecast,
) -> None:
    """Registra un modelo predictivo."""

    nombre = modelo.nombre.strip().upper()

    if not nombre:
        raise ValueError(
            "El modelo debe tener nombre."
        )

    _MODELOS[
        nombre
    ] = modelo


def obtener_modelo(
    nombre: str,
) -> ModeloForecast:
    """Obtiene un modelo registrado."""

    clave = nombre.strip().upper()

    if clave not in _MODELOS:
        disponibles = ", ".join(
            listar_modelos()
        )

        raise KeyError(
            f"Modelo no registrado: {nombre}. "
            f"Disponibles: {disponibles}"
        )

    return _MODELOS[
        clave
    ]


def listar_modelos() -> list[str]:
    """Lista modelos predictivos registrados."""

    return sorted(
        _MODELOS.keys()
    )