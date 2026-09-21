from motor_opciones.capturar_snapshot import (
    guardar_snapshot,
    actualizar_cadena,
)
from motor_opciones.comparar_snapshots import (
    ejecutar_comparacion,
    obtener_snapshots,
)


def main() -> None:
    """Captura mercado y compara contra el snapshot anterior."""

    snapshots_antes = obtener_snapshots()

    print()
    print("=" * 80)
    print("MONITOR OPTIONS FLOW - QQQ")
    print("=" * 80)

    actualizar_cadena()

    guardar_snapshot()

    if len(snapshots_antes) == 0:
        print()
        print(
            "Primer snapshot creado."
        )
        print(
            "Ejecuta de nuevo dentro de unos minutos."
        )
        return

    ejecutar_comparacion()


if __name__ == "__main__":
    main()