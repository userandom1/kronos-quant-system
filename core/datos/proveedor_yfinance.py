from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from core.activos.modelo_activo import Activo
from core.datos.cache_datos import CACHE_DATOS
from core.datos.errores import DatosNoDisponiblesError
from core.datos.normalizacion import (
    normalizar_ohlcv,
    normalizar_opciones,
)
from core.datos.proveedor_base import ProveedorDatos


class ProveedorYFinance(ProveedorDatos):
    """Adaptador robusto de datos para yfinance."""

    nombre = "YFINANCE"

    MAX_REINTENTOS = 3
    ESPERA_REINTENTO = 1.0

    TTL_HISTORICO = 900.0
    TTL_INTRADIA = 60.0
    TTL_VENCIMIENTOS = 300.0
    TTL_OPCIONES = 60.0

    def obtener_historico(
        self,
        activo: Activo,
        periodo: str = "5y",
        intervalo: str = "1d",
    ) -> pd.DataFrame:
        """Obtiene histórico OHLCV con caché y reintentos."""

        clave = (
            f"historico:"
            f"{activo.simbolo}:"
            f"{periodo}:"
            f"{intervalo}"
        )

        cache = CACHE_DATOS.obtener(
            clave
        )

        if isinstance(
            cache,
            pd.DataFrame,
        ):
            return cache

        ttl = (
            self.TTL_INTRADIA
            if intervalo.endswith(
                ("m", "h")
            )
            else self.TTL_HISTORICO
        )

        ultimo_error: Exception | None = None

        for intento in range(
            1,
            self.MAX_REINTENTOS + 1,
        ):
            try:
                datos = yf.download(
                    activo.simbolo,
                    period=periodo,
                    interval=intervalo,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                    timeout=20,
                )

                if not datos.empty:
                    resultado = normalizar_ohlcv(
                        datos=datos,
                        activo=activo,
                        proveedor=self.nombre,
                        intervalo=intervalo,
                    )

                    CACHE_DATOS.guardar(
                        clave,
                        resultado,
                        ttl,
                    )

                    return resultado

            except Exception as error:
                ultimo_error = error

            if intento < self.MAX_REINTENTOS:
                time.sleep(
                    self.ESPERA_REINTENTO
                    * intento
                )

        try:
            ticker = yf.Ticker(
                activo.simbolo
            )

            datos = ticker.history(
                period=periodo,
                interval=intervalo,
                auto_adjust=True,
                actions=False,
                timeout=20,
            )

            if not datos.empty:
                resultado = normalizar_ohlcv(
                    datos=datos,
                    activo=activo,
                    proveedor=self.nombre,
                    intervalo=intervalo,
                )

                CACHE_DATOS.guardar(
                    clave,
                    resultado,
                    ttl,
                )

                return resultado

        except Exception as error:
            ultimo_error = error

        mensaje = (
            f"No se pudieron descargar datos de "
            f"{activo.simbolo} tras "
            f"{self.MAX_REINTENTOS} intentos "
            "y fallback."
        )

        if ultimo_error is not None:
            mensaje += (
                f" Último error: "
                f"{ultimo_error}"
            )

        raise DatosNoDisponiblesError(
            mensaje
        )

    def obtener_intradia(
        self,
        activo: Activo,
        periodo: str = "5d",
        intervalo: str = "5m",
    ) -> pd.DataFrame:
        """Obtiene datos intradía."""

        return self.obtener_historico(
            activo=activo,
            periodo=periodo,
            intervalo=intervalo,
        )

    def obtener_precio_actual(
        self,
        activo: Activo,
    ) -> float:
        """Obtiene último cierre disponible."""

        datos = self.obtener_historico(
            activo=activo,
            periodo="5d",
            intervalo="1d",
        )

        cierre = datos[
            "close"
        ].dropna()

        if cierre.empty:
            raise DatosNoDisponiblesError(
                f"No existe precio válido para "
                f"{activo.simbolo}."
            )

        return float(
            cierre.iloc[-1]
        )

    def obtener_metadata(
        self,
        activo: Activo,
    ) -> dict[str, object]:
        """Obtiene metadatos auxiliares."""

        ticker = yf.Ticker(
            activo.simbolo
        )

        resultado: dict[str, object] = {
            "simbolo": activo.simbolo,
            "proveedor": self.nombre,
        }

        try:
            info = ticker.fast_info

            resultado.update(
                {
                    "divisa": self._leer_fast_info(
                        info,
                        "currency",
                    ),
                    "exchange": self._leer_fast_info(
                        info,
                        "exchange",
                    ),
                    "ultimo_precio": self._leer_fast_info(
                        info,
                        "last_price",
                    ),
                    "capitalizacion": self._leer_fast_info(
                        info,
                        "market_cap",
                    ),
                }
            )

        except Exception:
            pass

        return resultado

    def listar_vencimientos_opciones(
        self,
        activo: Activo,
    ) -> list[str]:
        """Lista vencimientos disponibles."""

        if not activo.capacidades.opciones:
            return []

        clave = (
            f"vencimientos:"
            f"{activo.simbolo}"
        )

        cache = CACHE_DATOS.obtener(
            clave
        )

        if isinstance(
            cache,
            list,
        ):
            return cache

        ticker = yf.Ticker(
            activo.simbolo
        )

        ultimo_error: Exception | None = None

        for intento in range(
            1,
            self.MAX_REINTENTOS + 1,
        ):
            try:
                vencimientos = list(
                    ticker.options
                )

                if vencimientos:
                    CACHE_DATOS.guardar(
                        clave,
                        vencimientos,
                        self.TTL_VENCIMIENTOS,
                    )

                    return vencimientos

            except Exception as error:
                ultimo_error = error

            if intento < self.MAX_REINTENTOS:
                time.sleep(
                    self.ESPERA_REINTENTO
                    * intento
                )

        if ultimo_error is not None:
            raise DatosNoDisponiblesError(
                f"No se pudieron obtener "
                f"vencimientos de "
                f"{activo.simbolo}. "
                f"Error: {ultimo_error}"
            )

        return []

    def obtener_cadena_opciones(
        self,
        activo: Activo,
        vencimiento: str,
    ) -> pd.DataFrame:
        """Obtiene calls y puts normalizados."""

        if not activo.capacidades.opciones:
            raise DatosNoDisponiblesError(
                f"{activo.simbolo} no tiene "
                "capacidad de opciones."
            )

        clave = (
            f"opciones:"
            f"{activo.simbolo}:"
            f"{vencimiento}"
        )

        cache = CACHE_DATOS.obtener(
            clave
        )

        if isinstance(
            cache,
            pd.DataFrame,
        ):
            return cache

        ticker = yf.Ticker(
            activo.simbolo
        )

        ultimo_error: Exception | None = None

        for intento in range(
            1,
            self.MAX_REINTENTOS + 1,
        ):
            try:
                cadena = ticker.option_chain(
                    vencimiento
                )

                calls = normalizar_opciones(
                    datos=cadena.calls,
                    activo=activo,
                    vencimiento=vencimiento,
                    tipo_opcion="CALL",
                    proveedor=self.nombre,
                )

                puts = normalizar_opciones(
                    datos=cadena.puts,
                    activo=activo,
                    vencimiento=vencimiento,
                    tipo_opcion="PUT",
                    proveedor=self.nombre,
                )

                resultado = pd.concat(
                    [
                        calls,
                        puts,
                    ],
                    ignore_index=True,
                )

                if not resultado.empty:
                    CACHE_DATOS.guardar(
                        clave,
                        resultado,
                        self.TTL_OPCIONES,
                    )

                    return resultado

            except Exception as error:
                ultimo_error = error

            if intento < self.MAX_REINTENTOS:
                time.sleep(
                    self.ESPERA_REINTENTO
                    * intento
                )

        mensaje = (
            f"No se pudo obtener la cadena de "
            f"{activo.simbolo} para "
            f"{vencimiento}."
        )

        if ultimo_error is not None:
            mensaje += (
                f" Último error: "
                f"{ultimo_error}"
            )

        raise DatosNoDisponiblesError(
            mensaje
        )

    @staticmethod
    def _leer_fast_info(
        info: object,
        clave: str,
    ) -> object | None:
        """Lee un campo de fast_info."""

        try:
            return getattr(
                info,
                clave,
            )

        except Exception:
            return None