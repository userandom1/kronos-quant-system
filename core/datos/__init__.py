"""Abstracción y gestión universal de datos."""

from core.datos.errores import (
    DatosNoDisponiblesError,
    ErrorProveedorDatos,
    ProveedorNoRegistradoError,
)
from core.datos.esquema_mercado import (
    COLUMNAS_OHLCV,
    COLUMNAS_OPCIONES,
    MetadatosMercado,
    validar_ohlcv,
    validar_opciones,
)
from core.datos.proveedor_base import ProveedorDatos
from core.datos.registro_proveedores import (
    listar_proveedores,
    obtener_proveedor,
    registrar_proveedor,
)

__all__ = [
    "COLUMNAS_OHLCV",
    "COLUMNAS_OPCIONES",
    "DatosNoDisponiblesError",
    "ErrorProveedorDatos",
    "MetadatosMercado",
    "ProveedorDatos",
    "ProveedorNoRegistradoError",
    "listar_proveedores",
    "obtener_proveedor",
    "registrar_proveedor",
    "validar_ohlcv",
    "validar_opciones",
]