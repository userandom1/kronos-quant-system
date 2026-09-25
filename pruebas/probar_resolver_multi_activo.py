from core.activos import resolver_activo


ACTIVOS_PRUEBA = [
    "QQQ",
    "AAPL",
    "SPY",
    "TLT",
    "GLD",
    "BTC-USD",
    "EURUSD=X",
    "NQ=F",
]


def imprimir_capacidades(
    capacidades: dict[str, bool],
) -> None:
    """Imprime las capacidades disponibles."""

    for nombre, disponible in capacidades.items():
        estado = "SI" if disponible else "NO"

        print(
            f"    {nombre:<24}: {estado}"
        )


def main() -> None:
    """Prueba el resolver multi-activo."""

    print("=" * 90)
    print("PRUEBA RESOLVER MULTI-ACTIVO")
    print("=" * 90)

    for simbolo in ACTIVOS_PRUEBA:
        activo = resolver_activo(
            simbolo
        )

        print()
        print(
            activo.resumen()
        )

        print(
            f"  Proveedor : {activo.proveedor}"
        )

        print(
            f"  Mercado   : {activo.mercado}"
        )

        print(
            f"  Divisa    : {activo.divisa}"
        )

        print(
            "  Capacidades:"
        )

        imprimir_capacidades(
            activo.capacidades.como_dict()
        )


if __name__ == "__main__":
    main()