from core.datos.errores import ProveedorNoRegistradoError
from core.datos.proveedor_base import ProveedorDatos
from core.datos.proveedor_yfinance import ProveedorYFinance


_PROVEEDORES: dict[
    str,
    ProveedorDatos,
] = {
    "YFINANCE": ProveedorYFinance(),
}


def obtener_proveedor(
    nombre: str,
) -> ProveedorDatos:
    """Obtiene un proveedor registrado."""

    clave = nombre.strip().upper()

    if clave not in _PROVEEDORES:
        raise ProveedorNoRegistradoError(
            f"Proveedor no registrado: {nombre}"
        )

    return _PROVEEDORES[
        clave
    ]


def registrar_proveedor(
    proveedor: ProveedorDatos,
) -> None:
    """Registra o sustituye un proveedor de datos."""

    nombre = proveedor.nombre.strip().upper()

    if not nombre:
        raise ValueError(
            "El proveedor debe tener un nombre."
        )

    _PROVEEDORES[
        nombre
    ] = proveedor


def listar_proveedores() -> list[str]:
    """Lista proveedores registrados."""

    return sorted(
        _PROVEEDORES.keys()
    )