from motor_mercado.estudio_regimen_v1 import (
    analizar_activo,
    guardar_resultado,
    imprimir_resultado,
)
from motor_mercado.resolver_activos import (
    resolver_activo,
)
from motor_mercado.universo_activos import (
    ASSET_GROUPS,
)


def si_no(
    valor: bool,
) -> str:
    """Convierte booleanos en texto legible."""

    return "Sí" if valor else "No"


def mostrar_ayuda() -> None:
    """Muestra los comandos disponibles."""

    print()
    print("COMANDOS")
    print("-" * 60)
    print("AYUDA             Mostrar ayuda")
    print("GRUPOS            Mostrar grupos")
    print("LISTA             Mostrar universo completo")
    print("LISTA <GRUPO>     Mostrar activos de un grupo")
    print("SALIR             Cerrar")
    print()
    print("También puedes escribir directamente un ticker.")
    print()
    print("Ejemplos:")
    print("  QQQ")
    print("  SPY")
    print("  NQ")
    print("  NQ1!")
    print("  BTC-USD")
    print("  EURUSD=X")
    print("  ^VIX")


def mostrar_grupos() -> None:
    """Muestra los grupos disponibles."""

    print()
    print("GRUPOS DISPONIBLES")
    print("-" * 60)

    for grupo in ASSET_GROUPS:
        print(
            f"{grupo:<30} "
            f"{len(ASSET_GROUPS[grupo]):>4} activos"
        )


def mostrar_lista(
    grupo: str | None = None,
) -> None:
    """Muestra el universo completo o un grupo concreto."""

    if grupo is not None:
        grupo = grupo.strip().upper()

        if grupo not in ASSET_GROUPS:
            print(
                f"\nGrupo no encontrado: {grupo}"
            )
            return

        print()
        print(grupo)
        print("-" * 60)

        print(
            ", ".join(
                ASSET_GROUPS[grupo]
            )
        )

        return

    for nombre_grupo, activos in ASSET_GROUPS.items():
        print()
        print(nombre_grupo)
        print("-" * 60)
        print(
            ", ".join(
                activos
            )
        )


def mostrar_activo(
    entrada: str,
) -> None:
    """Resuelve y muestra la información de un activo."""

    activo = resolver_activo(
        entrada
    )

    print()
    print("=" * 60)
    print("ACTIVO SELECCIONADO")
    print("=" * 60)

    print(
        f"Entrada usuario   : "
        f"{activo.entrada_usuario}"
    )

    print(
        f"Ticker datos      : "
        f"{activo.ticker}"
    )

    print(
        f"Tipo              : "
        f"{activo.tipo}"
    )

    print(
        f"Grupo             : "
        f"{activo.grupo}"
    )

    print(
        f"Benchmark         : "
        f"{activo.benchmark or 'No definido'}"
    )

    print()
    print("CAPACIDADES ACTUALES")
    print("-" * 60)

    print(
        f"Histórico         : "
        f"{si_no(activo.historico)}"
    )

    print(
        f"Market Regime     : "
        f"{si_no(activo.market_regime)}"
    )

    print(
        f"Kronos            : "
        f"{si_no(activo.kronos)}"
    )

    print(
        f"Options Chain     : "
        f"{si_no(activo.options_chain)}"
    )

    print(
        f"Dealer Engine     : "
        f"{si_no(activo.dealer_engine)}"
    )

    print(
        f"Portfolio         : "
        f"{si_no(activo.portfolio)}"
    )

    print()
    print("ANÁLISIS")
    print("-" * 60)
    print("[1] Market Regime")
    print("[2] Volver")

    opcion = input(
        "\nSelecciona opción: "
    ).strip()

    if opcion == "1":
        resultado = analizar_activo(
            entrada
        )

        imprimir_resultado(
            resultado
        )

        ruta = guardar_resultado(
            resultado
        )

        print()
        print(
            f"Guardado en: {ruta}"
        )


def main() -> None:
    """Ejecuta el selector interactivo."""

    print()
    print("=" * 60)
    print("MARKET INTELLIGENCE ENGINE")
    print("=" * 60)

    print(
        "Escribe AYUDA para ver los comandos."
    )

    while True:
        entrada = input(
            "\nTicker / comando: "
        ).strip()

        if not entrada:
            continue

        comando = entrada.upper()

        if comando == "SALIR":
            print("Cerrando.")
            return

        if comando == "AYUDA":
            mostrar_ayuda()
            continue

        if comando == "GRUPOS":
            mostrar_grupos()
            continue

        if comando == "LISTA":
            mostrar_lista()
            continue

        if comando.startswith(
            "LISTA "
        ):
            grupo = entrada[
                len("LISTA "):
            ]

            mostrar_lista(
                grupo
            )

            continue

        mostrar_activo(
            entrada
        )


if __name__ == "__main__":
    main()
