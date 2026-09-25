from enum import Enum


class ClaseActivo(str, Enum):
    """Clases principales de activos soportadas por la plataforma."""

    EQUITY = "EQUITY"
    ETF = "ETF"
    INDEX = "INDEX"
    FUTURE = "FUTURE"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    BOND = "BOND"
    COMMODITY = "COMMODITY"
    OPTION = "OPTION"
    UNKNOWN = "UNKNOWN"