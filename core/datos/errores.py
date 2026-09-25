class ErrorProveedorDatos(RuntimeError):
    """Error general producido por un proveedor de datos."""


class DatosNoDisponiblesError(ErrorProveedorDatos):
    """El proveedor no dispone de los datos solicitados."""


class ProveedorNoRegistradoError(ErrorProveedorDatos):
    """El proveedor solicitado no está registrado."""