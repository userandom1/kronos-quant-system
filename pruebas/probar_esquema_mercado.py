from core.activos import resolver_activo
from core.datos import (
    COLUMNAS_OHLCV,
    obtener_proveedor,
    validar_ohlcv,
)


ACTIVOS_PRUEBA = [
    "QQQ",
    "AAPL",
    "BTC-USD",
    "EURUSD=X",
    "NQ=F",
]


def main() -> None:
    """Comprueba el esquema universal multi-activo."""

    print("=" * 90)
    print("PRUEBA UNIVERSAL MARKET SCHEMA")
    print("=" * 90)

    for simbolo in ACTIVOS_PRUEBA:
        print()
        print("-" * 90)

        activo = resolver_activo(
            simbolo
        )

        proveedor = obtener_proveedor(
            activo.proveedor
        )

        print(
            activo.resumen()
        )

        try:
            datos = proveedor.obtener_historico(
                activo=activo,
                periodo="1mo",
                intervalo="1d",
            )

            validar_ohlcv(
                datos
            )

            print(
                "Esquema              : OK"
            )

            print(
                f"Columnas             : "
                f"{list(datos.columns)}"
            )

            print(
                f"Columnas esperadas   : "
                f"{COLUMNAS_OHLCV}"
            )

            print(
                f"Filas                : "
                f"{len(datos)}"
            )

            print(
                f"Desde                : "
                f"{datos.index.min()}"
            )

            print(
                f"Hasta                : "
                f"{datos.index.max()}"
            )

            print(
                f"Proveedor            : "
                f"{datos.attrs.get('proveedor')}"
            )

            print(
                f"Clase activo         : "
                f"{datos.attrs.get('clase_activo')}"
            )

            print(
                f"Divisa               : "
                f"{datos.attrs.get('divisa')}"
            )

            print(
                f"Último cierre        : "
                f"{datos['close'].iloc[-1]:,.4f}"
            )

        except Exception as error:
            print(
                f"ERROR                : "
                f"{type(error).__name__}: "
                f"{error}"
            )


if __name__ == "__main__":
    main()