from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from threading import RLock

import pandas as pd


@dataclass(slots=True)
class EntradaCache:
    """Entrada individual de la caché."""

    valor: object
    creado: float
    ttl: float


class CacheDatos:
    """Caché en memoria segura para datos de mercado."""

    def __init__(self) -> None:
        self._datos: dict[str, EntradaCache] = {}
        self._lock = RLock()

        self.hits = 0
        self.misses = 0

    def obtener(
        self,
        clave: str,
    ) -> object | None:
        """Obtiene un valor si sigue vigente."""

        with self._lock:
            entrada = self._datos.get(
                clave
            )

            if entrada is None:
                self.misses += 1
                return None

            edad = (
                time.time()
                - entrada.creado
            )

            if edad > entrada.ttl:
                del self._datos[
                    clave
                ]

                self.misses += 1
                return None

            self.hits += 1

            return self._copiar(
                entrada.valor
            )

    def guardar(
        self,
        clave: str,
        valor: object,
        ttl: float,
    ) -> None:
        """Guarda un valor en caché."""

        with self._lock:
            self._datos[
                clave
            ] = EntradaCache(
                valor=self._copiar(
                    valor
                ),
                creado=time.time(),
                ttl=ttl,
            )

    def limpiar(
        self,
    ) -> None:
        """Vacía completamente la caché."""

        with self._lock:
            self._datos.clear()

            self.hits = 0
            self.misses = 0

    def estadisticas(
        self,
    ) -> dict[str, int]:
        """Devuelve estadísticas de uso."""

        with self._lock:
            return {
                "entradas": len(
                    self._datos
                ),
                "hits": self.hits,
                "misses": self.misses,
            }

    @staticmethod
    def _copiar(
        valor: object,
    ) -> object:
        """Evita modificar accidentalmente el objeto cacheado."""

        if isinstance(
            valor,
            pd.DataFrame,
        ):
            copia = valor.copy(
                deep=True
            )

            copia.attrs = (
                valor.attrs.copy()
            )

            return copia

        if isinstance(
            valor,
            pd.Series,
        ):
            return valor.copy(
                deep=True
            )

        return copy.deepcopy(
            valor
        )


CACHE_DATOS = CacheDatos()