from __future__ import annotations


UNIVERSOS: dict[str, list[str]] = {
    "US_TECH": [
        "QQQ",
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "META",
        "AVGO",
        "SMH",
        "XLK",
    ],
    "ETF_GLOBALES": [
        "SPY",
        "QQQ",
        "IWM",
        "EFA",
        "EEM",
        "TLT",
        "GLD",
        "VNQ",
    ],
    "CRIPTO": [
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
    ],
    "FOREX": [
        "EURUSD=X",
        "GBPUSD=X",
        "USDJPY=X",
        "AUDUSD=X",
    ],
    "FUTUROS": [
        "ES=F",
        "NQ=F",
        "YM=F",
        "RTY=F",
        "CL=F",
        "GC=F",
    ],
    "MACRO": [
        "SPY",
        "QQQ",
        "IWM",
        "TLT",
        "GLD",
        "HYG",
        "LQD",
        "^VIX",
    ],
}


def listar_universos() -> list[str]:
    """Devuelve los universos disponibles."""

    return sorted(
        UNIVERSOS.keys()
    )


def obtener_universo(
    nombre: str,
) -> list[str]:
    """Devuelve los activos de un universo."""

    clave = nombre.strip().upper()

    if clave not in UNIVERSOS:
        disponibles = ", ".join(
            listar_universos()
        )

        raise KeyError(
            f"Universo no encontrado: {nombre}. "
            f"Disponibles: {disponibles}"
        )

    return UNIVERSOS[
        clave
    ].copy()


def registrar_universo(
    nombre: str,
    simbolos: list[str],
) -> None:
    """Registra un universo en memoria."""

    clave = nombre.strip().upper()

    activos = [
        simbolo.strip().upper()
        for simbolo in simbolos
        if simbolo.strip()
    ]

    if not clave:
        raise ValueError(
            "El nombre no puede estar vacío."
        )

    if not activos:
        raise ValueError(
            "El universo debe contener activos."
        )

    UNIVERSOS[
        clave
    ] = activos