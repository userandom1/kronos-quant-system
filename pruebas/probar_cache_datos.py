from __future__ import annotations

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from core.datos.cache_datos import CACHE_DATOS


def main() -> None:
    """Comprueba que la caché evita descargas repetidas."""

    CACHE_DATOS.limpiar()

    activo = resolver_activo(
        "SPY"
    )

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    proveedor.obtener_historico(
        activo,
        periodo="1mo",
        intervalo="1d",
    )

    primera = CACHE_DATOS.estadisticas()

    proveedor.obtener_historico(
        activo,
        periodo="1mo",
        intervalo="1d",
    )

    segunda = CACHE_DATOS.estadisticas()

    if segunda[
        "hits"
    ] <= primera[
        "hits"
    ]:
        raise AssertionError(
            "La caché no registró un hit."
        )

    print(
        "CACHE UNIVERSAL: OK"
    )

    print(
        segunda
    )


if __name__ == "__main__":
    main()