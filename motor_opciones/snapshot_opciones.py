from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


RUTA_BASE = Path(
    __file__
).resolve().parents[1]


def guardar_snapshot(
    simbolo: str,
    cadena: pd.DataFrame,
) -> Path:
    """Guarda un snapshot universal de opciones."""

    simbolo_limpio = (
        simbolo
        .replace(
            "=",
            "_",
        )
        .replace(
            "^",
            "",
        )
    )

    ruta = (
        RUTA_BASE
        / "resultados"
        / "options_flow_universal"
        / simbolo_limpio
        / "snapshots"
    )

    ruta.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    archivo = (
        ruta
        / f"snapshot_{timestamp}.csv"
    )

    cadena.to_csv(
        archivo,
        index=False,
    )

    return archivo


def obtener_ultimos_snapshots(
    simbolo: str,
    cantidad: int = 2,
) -> list[Path]:
    """Obtiene los snapshots más recientes."""

    simbolo_limpio = (
        simbolo
        .replace(
            "=",
            "_",
        )
        .replace(
            "^",
            "",
        )
    )

    ruta = (
        RUTA_BASE
        / "resultados"
        / "options_flow_universal"
        / simbolo_limpio
        / "snapshots"
    )

    if not ruta.exists():
        return []

    archivos = sorted(
        ruta.glob(
            "snapshot_*.csv"
        ),
        key=lambda archivo: (
            archivo.stat().st_mtime
        ),
        reverse=True,
    )

    return archivos[
        :cantidad
    ]