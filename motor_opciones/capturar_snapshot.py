from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_CADENA_FILTRADA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "cadena_filtrada.csv"
)

RUTA_SNAPSHOTS = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "snapshots"
)


def actualizar_cadena() -> None:
    """Descarga y limpia una nueva cadena de opciones."""

    print("Actualizando cadena real de QQQ...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "motor_opciones.cadena_real_qqq",
        ],
        cwd=RUTA_BASE,
        check=True,
    )

    print("Limpiando cadena...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "motor_opciones.limpieza_cadena",
        ],
        cwd=RUTA_BASE,
        check=True,
    )


def guardar_snapshot() -> Path:
    """Guarda una copia temporal de la cadena filtrada."""

    if not RUTA_CADENA_FILTRADA.exists():
        raise FileNotFoundError(
            f"No existe: {RUTA_CADENA_FILTRADA}"
        )

    RUTA_SNAPSHOTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ahora = datetime.now()

    nombre = (
        "snapshot_"
        f"{ahora:%Y%m%d_%H%M%S}.csv"
    )

    destino = (
        RUTA_SNAPSHOTS
        / nombre
    )

    shutil.copy2(
        RUTA_CADENA_FILTRADA,
        destino,
    )

    datos = pd.read_csv(
        destino
    )

    print()
    print("=" * 72)
    print("SNAPSHOT GUARDADO")
    print("=" * 72)
    print(
        f"Contratos : {len(datos):,}"
    )
    print(
        f"Archivo   : {destino}"
    )

    return destino


def main() -> None:
    """Actualiza la cadena y captura un snapshot."""

    actualizar_cadena()
    guardar_snapshot()


if __name__ == "__main__":
    main()