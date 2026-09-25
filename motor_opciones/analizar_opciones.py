from __future__ import annotations

import sys
from pathlib import Path

from core.activos import resolver_activo
from motor_opciones.options_engine_universal import (
    ejecutar_options_engine,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "options_engine_universal"
)


def main() -> None:
    """Ejecuta Options Engine Universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_opciones.analizar_opciones "
            "ACTIVO [VENCIMIENTO]"
        )

    simbolo = sys.argv[
        1
    ]

    vencimiento = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else None
    )

    activo = resolver_activo(
        simbolo
    )

    resultado = ejecutar_options_engine(
        activo=activo,
        vencimiento=vencimiento,
    )

    print(
        "=" * 90
    )

    print(
        "OPTIONS ENGINE UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        f"Activo             : "
        f"{resultado.activo.simbolo}"
    )

    print(
        f"Clase              : "
        f"{resultado.activo.clase.value}"
    )

    print(
        f"Spot               : "
        f"{resultado.spot:,.4f}"
    )

    print(
        f"Vencimiento        : "
        f"{resultado.vencimiento}"
    )

    print(
        f"Contratos          : "
        f"{resultado.resumen['contratos']}"
    )

    print(
        f"Volumen total      : "
        f"{resultado.resumen['volumen_total']:,}"
    )

    print(
        f"OI total           : "
        f"{resultado.resumen['oi_total']:,}"
    )

    print(
        f"Put/Call volumen   : "
        f"{resultado.resumen['put_call_volumen']:.3f}"
    )

    print(
        f"Put/Call OI        : "
        f"{resultado.resumen['put_call_oi']:.3f}"
    )

    print(
        f"Premium proxy      : "
        f"${resultado.resumen['premium_total']:,.2f}"
    )

    print(
        f"IV media calls     : "
        f"{resultado.resumen['iv_media_calls']:.4f}"
    )

    print(
        f"IV media puts      : "
        f"{resultado.resumen['iv_media_puts']:.4f}"
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta = (
        RUTA_RESULTADOS
        / f"{activo.simbolo.replace('=', '_')}"
        f"_{resultado.vencimiento}.csv"
    )

    resultado.cadena.to_csv(
        ruta,
        index=False,
    )

    print()
    print(
        f"Cadena guardada    : {ruta}"
    )


if __name__ == "__main__":
    main()