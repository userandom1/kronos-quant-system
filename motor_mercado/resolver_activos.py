from dataclasses import dataclass

from motor_mercado.universo_activos import (
    ALIASES,
    ASSET_GROUPS,
    BENCHMARKS,
    DEALER_ENGINE_IMPLEMENTADO,
)


@dataclass(frozen=True)
class ActivoResuelto:
    """Representa un activo normalizado dentro del universo."""

    entrada_usuario: str
    ticker: str
    tipo: str
    grupo: str
    benchmark: str | None
    historico: bool
    market_regime: bool
    kronos: bool
    options_chain: bool
    dealer_engine: bool
    portfolio: bool


def normalizar_ticker(
    ticker_usuario: str,
) -> str:
    """Normaliza el ticker y aplica aliases conocidos."""

    ticker = (
        ticker_usuario
        .strip()
        .upper()
    )

    return ALIASES.get(
        ticker,
        ticker,
    )


def buscar_grupo(
    ticker_usuario: str,
    ticker_normalizado: str,
) -> str:
    """Busca el grupo al que pertenece el activo."""

    candidatos = {
        ticker_usuario.strip().upper(),
        ticker_normalizado,
    }

    for grupo, activos in ASSET_GROUPS.items():
        for activo in activos:
            if activo.upper() in candidatos:
                return grupo

            activo_normalizado = ALIASES.get(
                activo.upper(),
                activo.upper(),
            )

            if activo_normalizado in candidatos:
                return grupo

    return "NO_CLASIFICADO"


def detectar_tipo(
    ticker: str,
    grupo: str,
) -> str:
    """Detecta el tipo principal del activo."""

    if ticker.endswith("-USD"):
        return "CRYPTO"

    if ticker.endswith("=F"):
        return "FUTURE"

    if ticker.endswith("=X"):
        return "FOREX"

    if ticker.startswith("^"):
        if grupo == "VOLATILITY":
            return "VOLATILITY_INDEX"

        return "INDEX"

    if grupo == "MAJOR_STOCKS":
        return "STOCK"

    if "ETF" in grupo:
        return "ETF"

    return "EQUITY_OR_FUND"


def capacidades_por_tipo(
    ticker: str,
    tipo: str,
) -> dict[str, bool]:
    """Devuelve las capacidades actualmente disponibles."""

    historico = tipo in {
        "ETF",
        "STOCK",
        "FUTURE",
        "CRYPTO",
        "FOREX",
        "INDEX",
        "VOLATILITY_INDEX",
        "EQUITY_OR_FUND",
    }

    market_regime = historico

    kronos = tipo in {
        "ETF",
        "STOCK",
        "FUTURE",
        "CRYPTO",
        "FOREX",
        "INDEX",
        "EQUITY_OR_FUND",
    }

    options_chain = ticker in {
        "QQQ",
    }

    dealer_engine = (
        ticker
        in DEALER_ENGINE_IMPLEMENTADO
    )

    portfolio = tipo in {
        "ETF",
        "STOCK",
        "CRYPTO",
        "FUTURE",
    }

    return {
        "historico": historico,
        "market_regime": market_regime,
        "kronos": kronos,
        "options_chain": options_chain,
        "dealer_engine": dealer_engine,
        "portfolio": portfolio,
    }


def resolver_activo(
    entrada_usuario: str,
) -> ActivoResuelto:
    """Resuelve completamente un ticker introducido por el usuario."""

    ticker = normalizar_ticker(
        entrada_usuario
    )

    grupo = buscar_grupo(
        entrada_usuario,
        ticker,
    )

    tipo = detectar_tipo(
        ticker,
        grupo,
    )

    capacidades = capacidades_por_tipo(
        ticker,
        tipo,
    )

    benchmark = BENCHMARKS.get(
        ticker
    )

    return ActivoResuelto(
        entrada_usuario=entrada_usuario,
        ticker=ticker,
        tipo=tipo,
        grupo=grupo,
        benchmark=benchmark,
        historico=capacidades["historico"],
        market_regime=capacidades["market_regime"],
        kronos=capacidades["kronos"],
        options_chain=capacidades["options_chain"],
        dealer_engine=capacidades["dealer_engine"],
        portfolio=capacidades["portfolio"],
    )