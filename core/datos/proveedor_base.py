from abc import ABC, abstractmethod

import pandas as pd

from core.activos.modelo_activo import Activo


class ProveedorDatos(ABC):
    """
    Interfaz común para todos los proveedores de datos.

    Los motores cuantitativos deben consumir esta interfaz
    en lugar de depender directamente de una API concreta.
    """

    nombre: str

    @abstractmethod
    def obtener_historico(
        self,
        activo: Activo,
        periodo: str = "5y",
        intervalo: str = "1d",
    ) -> pd.DataFrame:
        """Obtiene histórico OHLCV del activo."""

    @abstractmethod
    def obtener_intradia(
        self,
        activo: Activo,
        periodo: str = "5d",
        intervalo: str = "5m",
    ) -> pd.DataFrame:
        """Obtiene datos intradía del activo."""

    @abstractmethod
    def obtener_precio_actual(
        self,
        activo: Activo,
    ) -> float:
        """Obtiene el último precio disponible."""

    @abstractmethod
    def obtener_metadata(
        self,
        activo: Activo,
    ) -> dict[str, object]:
        """Obtiene metadatos básicos del activo."""

    @abstractmethod
    def listar_vencimientos_opciones(
        self,
        activo: Activo,
    ) -> list[str]:
        """Lista vencimientos disponibles de opciones."""

    @abstractmethod
    def obtener_cadena_opciones(
        self,
        activo: Activo,
        vencimiento: str,
    ) -> pd.DataFrame:
        """Obtiene la cadena de opciones de un vencimiento."""