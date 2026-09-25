from core.activos.capacidades import CapacidadesActivo
from core.activos.clases_activo import ClaseActivo
from core.activos.modelo_activo import Activo


ETF_CONOCIDOS = {
    "QQQ",
    "SPY",
    "IWM",
    "SMH",
    "SOXX",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLP",
    "XLI",
    "XLU",
    "XLRE",
    "XLB",
    "TLT",
    "IEF",
    "SHY",
    "HYG",
    "LQD",
    "GLD",
    "SLV",
    "VNQ",
    "EFA",
    "EEM",
}

INDICES_CONOCIDOS = {
    "^GSPC": "SPY",
    "^NDX": "QQQ",
    "^DJI": "DIA",
    "^RUT": "IWM",
    "^VIX": "SPY",
}

FOREX_CONOCIDOS = {
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "AUDUSD=X",
    "USDCAD=X",
    "USDCHF=X",
    "NZDUSD=X",
}

CRIPTO_CONOCIDOS = {
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
}

FUTUROS_CONOCIDOS = {
    "ES=F": "SPY",
    "NQ=F": "QQQ",
    "YM=F": "DIA",
    "RTY=F": "IWM",
    "CL=F": "USO",
    "GC=F": "GLD",
    "SI=F": "SLV",
    "ZB=F": "TLT",
}

COMMODITIES_CONOCIDOS = {
    "CL=F",
    "GC=F",
    "SI=F",
}

BENCHMARKS_ESPECIFICOS = {
    "QQQ": "SPY",
    "SMH": "QQQ",
    "SOXX": "QQQ",
    "XLK": "SPY",
    "IWM": "SPY",
    "TLT": "SPY",
    "IEF": "SPY",
    "SHY": "SPY",
    "HYG": "SPY",
    "LQD": "SPY",
    "GLD": "SPY",
    "SLV": "SPY",
    "VNQ": "SPY",
    "EFA": "SPY",
    "EEM": "SPY",
}


def detectar_clase(
    simbolo: str,
) -> ClaseActivo:
    """Detecta la clase de activo mediante reglas simples."""

    simbolo = simbolo.upper()

    if simbolo in ETF_CONOCIDOS:
        return ClaseActivo.ETF

    if simbolo in INDICES_CONOCIDOS:
        return ClaseActivo.INDEX

    if simbolo in FOREX_CONOCIDOS:
        return ClaseActivo.FOREX

    if simbolo in CRIPTO_CONOCIDOS:
        return ClaseActivo.CRYPTO

    if simbolo in FUTUROS_CONOCIDOS:
        if simbolo in COMMODITIES_CONOCIDOS:
            return ClaseActivo.COMMODITY

        return ClaseActivo.FUTURE

    if simbolo.endswith("=X"):
        return ClaseActivo.FOREX

    if simbolo.endswith("-USD"):
        return ClaseActivo.CRYPTO

    if simbolo.endswith("=F"):
        return ClaseActivo.FUTURE

    if simbolo.startswith("^"):
        return ClaseActivo.INDEX

    return ClaseActivo.EQUITY


def resolver_benchmark(
    simbolo: str,
    clase: ClaseActivo,
) -> str:
    """Determina un benchmark razonable para el activo."""

    simbolo = simbolo.upper()

    if simbolo in BENCHMARKS_ESPECIFICOS:
        return BENCHMARKS_ESPECIFICOS[
            simbolo
        ]

    if simbolo in INDICES_CONOCIDOS:
        return INDICES_CONOCIDOS[
            simbolo
        ]

    if simbolo in FUTUROS_CONOCIDOS:
        return FUTUROS_CONOCIDOS[
            simbolo
        ]

    if clase == ClaseActivo.CRYPTO:
        if simbolo == "BTC-USD":
            return "BTC-USD"

        return "BTC-USD"

    if clase == ClaseActivo.FOREX:
        return "DX-Y.NYB"

    if clase == ClaseActivo.ETF:
        return "SPY"

    if clase == ClaseActivo.EQUITY:
        return "SPY"

    if clase == ClaseActivo.INDEX:
        return "SPY"

    if clase == ClaseActivo.BOND:
        return "IEF"

    if clase == ClaseActivo.COMMODITY:
        return "DBC"

    return "SPY"


def resolver_divisa(
    simbolo: str,
    clase: ClaseActivo,
) -> str:
    """Determina la divisa base de análisis."""

    simbolo = simbolo.upper()

    if clase == ClaseActivo.FOREX:
        if len(simbolo) >= 6:
            return simbolo[
                3:6
            ]

    if clase == ClaseActivo.CRYPTO:
        if simbolo.endswith(
            "-USD"
        ):
            return "USD"

    return "USD"


def resolver_mercado(
    simbolo: str,
    clase: ClaseActivo,
) -> str:
    """Asigna un mercado lógico para la primera versión."""

    simbolo = simbolo.upper()

    if clase == ClaseActivo.CRYPTO:
        return "CRYPTO"

    if clase == ClaseActivo.FOREX:
        return "FOREX"

    if clase == ClaseActivo.FUTURE:
        return "FUTURES"

    if clase == ClaseActivo.COMMODITY:
        return "FUTURES"

    if clase == ClaseActivo.INDEX:
        return "INDEX"

    if simbolo in {
        "QQQ",
        "SMH",
        "SOXX",
        "XLK",
    }:
        return "NASDAQ_US"

    return "US"


def resolver_capacidades(
    clase: ClaseActivo,
) -> CapacidadesActivo:
    """Resuelve las capacidades iniciales por clase de activo."""

    if clase in {
        ClaseActivo.EQUITY,
        ClaseActivo.ETF,
        ClaseActivo.INDEX,
    }:
        return CapacidadesActivo(
            historico=True,
            intradia=True,
            senales=True,
            portfolio=True,
            riesgo=True,
            opciones=True,
            options_flow=True,
            dealer_engine=True,
            forecast=True,
            volatilidad_implicita=True,
            superficie_volatilidad=True,
        )

    if clase in {
        ClaseActivo.FUTURE,
        ClaseActivo.COMMODITY,
    }:
        return CapacidadesActivo(
            historico=True,
            intradia=True,
            senales=True,
            portfolio=True,
            riesgo=True,
            opciones=False,
            options_flow=False,
            dealer_engine=False,
            forecast=True,
            volatilidad_implicita=False,
            superficie_volatilidad=False,
        )

    if clase == ClaseActivo.CRYPTO:
        return CapacidadesActivo(
            historico=True,
            intradia=True,
            senales=True,
            portfolio=True,
            riesgo=True,
            opciones=False,
            options_flow=False,
            dealer_engine=False,
            forecast=True,
            volatilidad_implicita=False,
            superficie_volatilidad=False,
        )

    if clase == ClaseActivo.FOREX:
        return CapacidadesActivo(
            historico=True,
            intradia=True,
            senales=True,
            portfolio=True,
            riesgo=True,
            opciones=False,
            options_flow=False,
            dealer_engine=False,
            forecast=True,
            volatilidad_implicita=False,
            superficie_volatilidad=False,
        )

    return CapacidadesActivo()


def resolver_activo(
    simbolo: str,
) -> Activo:
    """
    Convierte un símbolo en un objeto Activo universal.

    Esta primera versión utiliza reglas deterministas.
    En fases posteriores se enriquecerá mediante proveedores de datos.
    """

    simbolo = simbolo.strip().upper()

    if not simbolo:
        raise ValueError(
            "El símbolo no puede estar vacío."
        )

    clase = detectar_clase(
        simbolo
    )

    benchmark = resolver_benchmark(
        simbolo,
        clase,
    )

    divisa = resolver_divisa(
        simbolo,
        clase,
    )

    mercado = resolver_mercado(
        simbolo,
        clase,
    )

    capacidades = resolver_capacidades(
        clase
    )

    return Activo(
        simbolo=simbolo,
        clase=clase,
        benchmark=benchmark,
        divisa=divisa,
        proveedor="YFINANCE",
        mercado=mercado,
        capacidades=capacidades,
    )