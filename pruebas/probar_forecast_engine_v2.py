from __future__ import annotations

from core.modelos.registro_modelos import (
    listar_modelos,
)


def main() -> None:
    """Comprueba el registro de modelos."""

    modelos = listar_modelos()

    esperados = {
        "DRIFT",
        "MOMENTUM",
        "KRONOS",
    }

    encontrados = set(
        modelos
    )

    faltantes = (
        esperados
        - encontrados
    )

    if faltantes:
        raise AssertionError(
            f"Faltan modelos: {faltantes}"
        )

    print(
        f"Modelos registrados: {modelos}"
    )

    print(
        "FORECAST ENGINE V2: OK"
    )


if __name__ == "__main__":
    main()