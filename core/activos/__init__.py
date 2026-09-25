"""Modelos y resolución universal de activos."""

from core.activos.capacidades import CapacidadesActivo
from core.activos.clases_activo import ClaseActivo
from core.activos.modelo_activo import Activo
from core.activos.resolver_activo import resolver_activo

__all__ = [
    "Activo",
    "CapacidadesActivo",
    "ClaseActivo",
    "resolver_activo",
]