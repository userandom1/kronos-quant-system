from core.activos import resolver_activo
from core.datos import (
    listar_proveedores,
    obtener_proveedor,
)


ACTIVOS_PRUEBA = [
    "QQQ",
    "AAPL",
    "BTC-USD",
    "EURUSD=X",
    "NQ=F",
]


def main() -> None:
    """Prueba la abstracción universal de datos."""

    print(
        "=" * 90
    )
    print(
        "PRUEBA DATA PROVIDER ABSTRACTION"
    )
    print(
        "=" * 90
    )

    print()
    print(
        f"Proveedores registrados: "
        f"{listar_proveedores()}"
    )

    for simbolo in ACTIVOS_PRUEBA:
        print()
        print(
            "-" * 90
        )

        activo = resolver_activo(
            simbolo
        )

        proveedor = obtener_proveedor(
            activo.proveedor
        )

        print(
            activo.resumen()
        )

        print(
            f"Proveedor seleccionado : "
            f"{proveedor.nombre}"
        )

        try:
            datos = proveedor.obtener_historico(
                activo=activo,
                periodo="1mo",
                intervalo="1d",
            )

            print(
                f"Filas recibidas        : "
                f"{len(datos)}"
            )

            print(
                f"Columnas               : "
                f"{list(datos.columns)}"
            )

            precio = proveedor.obtener_precio_actual(
                activo
            )

            print(
                f"Último precio          : "
                f"{precio:,.4f}"
            )

        except Exception as error:
            print(
                f"ERROR                  : "
                f"{error}"
            )


if __name__ == "__main__":
    main()