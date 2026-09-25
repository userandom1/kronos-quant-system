from __future__ import annotations

from motor_sistema.comprobar_sistema_v2 import (
    comprobar_sistema,
)


def main() -> None:
    """Prueba mínima de Release V2."""

    correcto, resultados = (
        comprobar_sistema(
            comprobar_datos=True
        )
    )

    for resultado in resultados:
        print(
            f"{resultado.componente:<20} | "
            f"{resultado.estado}"
        )

    if not correcto:
        raise SystemExit(
            "HEALTH CHECK V2: ERROR"
        )

    print()
    print(
        "RELEASE V2 BASE: OK"
    )


if __name__ == "__main__":
    main()