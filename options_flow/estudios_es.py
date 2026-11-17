"""GEX/DEX hipotéticos de SPX alineados con un gráfico de ES."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable, Mapping


def _hora(valor: str) -> datetime:
    fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if fecha.tzinfo is None or fecha.utcoffset() is None:
        raise ValueError("hora_sin_zona")
    return fecha


def calcular_estudio(
    contratos: Iterable[Mapping[str, object]],
    *,
    spx_referencia: float,
    es_referencia: float,
    spx_hora_utc: str,
    es_hora_utc: str,
    max_desfase_minutos: int = 5,
) -> list[dict[str, float]]:
    """Agrega exposición por strike; calls cortas y puts largas es solo un escenario.

    GEX: USD de cambio de Delta ante un movimiento del 1% del SPX.
    DEX: USD nocionales de Delta. El nivel ES usa un desplazamiento de referencias.
    """
    if not all(math.isfinite(x) and x > 0 for x in (spx_referencia, es_referencia)):
        raise ValueError("referencia_invalida")
    desfase = abs(_hora(spx_hora_utc) - _hora(es_hora_utc))
    if desfase > timedelta(minutes=max_desfase_minutos):
        raise ValueError("referencias_no_sincronizadas")
    base = es_referencia - spx_referencia
    grupos: dict[float, list[float]] = defaultdict(lambda: [0.0, 0.0])
    total = 0
    for fila in contratos:
        tipo = str(fila["tipo"]).upper()
        strike = float(fila["strike"])
        oi_valor = float(fila["open_interest"])
        delta = float(fila["delta"])
        gamma = float(fila["gamma"])
        multiplicador_valor = float(fila["multiplicador"])
        if (
            tipo not in {"CALL", "PUT"} or strike <= 0 or oi_valor < 0
            or not math.isfinite(oi_valor) or not oi_valor.is_integer()
            or not math.isfinite(multiplicador_valor) or multiplicador_valor != 100
            or not all(math.isfinite(x) for x in (strike, delta, gamma))
            or gamma < 0 or not (-1 <= delta <= 1)
            or (tipo == "CALL" and delta < 0) or (tipo == "PUT" and delta > 0)
        ):
            raise ValueError("contrato_spx_invalido")
        oi = int(oi_valor)
        multiplicador = int(multiplicador_valor)
        signo_dealer = -1 if tipo == "CALL" else 1
        grupos[strike][0] += signo_dealer * gamma * oi * multiplicador * spx_referencia**2 * 0.01
        grupos[strike][1] += signo_dealer * delta * oi * multiplicador * spx_referencia
        total += 1
    if total == 0:
        raise ValueError("sin_contratos_spx")
    return [
        {"strike_spx": strike, "nivel_es_proxy": strike + base,
         "gex_usd_por_1pct": valores[0], "dex_usd": valores[1]}
        for strike, valores in sorted(grupos.items())
    ]
