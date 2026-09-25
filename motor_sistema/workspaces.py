from __future__ import annotations

import json
from pathlib import Path


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_CONFIGURACION = (
    RUTA_BASE
    / "configuracion"
)

ARCHIVO_WATCHLISTS = (
    RUTA_CONFIGURACION
    / "watchlists.json"
)


WATCHLISTS_INICIALES = {
    "PRINCIPAL": [
        "QQQ",
        "SPY",
        "AAPL",
        "NVDA",
        "GLD",
        "TLT",
    ],
    "MACRO": [
        "SPY",
        "QQQ",
        "IWM",
        "TLT",
        "GLD",
        "HYG",
        "^VIX",
    ],
    "CRIPTO": [
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
    ],
}


def inicializar_watchlists() -> None:
    """Crea la configuración inicial si no existe."""

    RUTA_CONFIGURACION.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ARCHIVO_WATCHLISTS.exists():
        return

    guardar_watchlists(
        WATCHLISTS_INICIALES
    )


def cargar_watchlists() -> dict[str, list[str]]:
    """Carga las watchlists persistentes."""

    inicializar_watchlists()

    with ARCHIVO_WATCHLISTS.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        datos = json.load(
            archivo
        )

    return {
        str(nombre).upper(): [
            str(simbolo).upper()
            for simbolo in simbolos
        ]
        for nombre, simbolos in datos.items()
    }


def guardar_watchlists(
    watchlists: dict[str, list[str]],
) -> None:
    """Guarda todas las watchlists."""

    RUTA_CONFIGURACION.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ARCHIVO_WATCHLISTS.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            watchlists,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def obtener_watchlist(
    nombre: str,
) -> list[str]:
    """Obtiene una watchlist."""

    watchlists = cargar_watchlists()

    clave = nombre.strip().upper()

    if clave not in watchlists:
        raise KeyError(
            f"Watchlist no encontrada: {nombre}"
        )

    return watchlists[
        clave
    ].copy()


def guardar_watchlist(
    nombre: str,
    simbolos: list[str],
) -> None:
    """Crea o sustituye una watchlist."""

    clave = nombre.strip().upper()

    activos = list(
        dict.fromkeys(
            simbolo.strip().upper()
            for simbolo in simbolos
            if simbolo.strip()
        )
    )

    if not clave:
        raise ValueError(
            "Nombre de watchlist vacío."
        )

    if not activos:
        raise ValueError(
            "La watchlist debe contener activos."
        )

    watchlists = cargar_watchlists()

    watchlists[
        clave
    ] = activos

    guardar_watchlists(
        watchlists
    )


def eliminar_watchlist(
    nombre: str,
) -> None:
    """Elimina una watchlist."""

    clave = nombre.strip().upper()

    watchlists = cargar_watchlists()

    if clave not in watchlists:
        raise KeyError(
            f"Watchlist no encontrada: {nombre}"
        )

    del watchlists[
        clave
    ]

    guardar_watchlists(
        watchlists
    )