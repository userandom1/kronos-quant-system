from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "sistema"
)


@dataclass(frozen=True)
class Componente:
    """Archivo requerido por Kronos Release V1."""

    nombre: str
    ruta: Path
    critico: bool = True


COMPONENTES = [
    Componente(
        nombre="Market Regime V2",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "regimen_mercado_v2"
            / "regimen_global.csv"
        ),
    ),
    Componente(
        nombre="Señales V2",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "senales_v2"
            / "senales_v2.csv"
        ),
    ),
    Componente(
        nombre="Portfolio V2 - Pesos",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "portfolio_engine"
            / "v1"
            / "v2"
            / "pesos_portfolio_v2.csv"
        ),
    ),
    Componente(
        nombre="Risk Engine V1",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "risk_engine"
            / "v1"
            / "metricas_riesgo.csv"
        ),
    ),
    Componente(
        nombre="Cadena QQQ limpia",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "dealer_engine"
            / "QQQ"
            / "cadena_filtrada.csv"
        ),
    ),
    Componente(
        nombre="Options Flow V2",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "options_flow"
            / "QQQ"
            / "v2"
            / "resumen_flow_v2.csv"
        ),
        critico=False,
    ),
    Componente(
        nombre="Dealer Engine V4",
        ruta=(
            RUTA_BASE
            / "resultados"
            / "dealer_engine"
            / "QQQ"
            / "v4"
            / "resumen_dealer_v4.csv"
        ),
        critico=False,
    ),
]


def analizar_componente(
    componente: Componente,
) -> dict:
    """Comprueba disponibilidad y antigüedad."""

    ruta = componente.ruta

    if not ruta.exists():
        return {
            "componente": componente.nombre,
            "critico": componente.critico,
            "existe": False,
            "tamano_kb": None,
            "filas": None,
            "modificado": None,
            "edad_horas": None,
            "estado": "NO_DISPONIBLE",
            "ruta": str(ruta),
        }

    stat = ruta.stat()

    modificacion = datetime.fromtimestamp(
        stat.st_mtime
    )

    edad_horas = (
        datetime.now()
        - modificacion
    ).total_seconds() / 3600.0

    filas = None

    try:
        datos = pd.read_csv(
            ruta
        )

        filas = len(
            datos
        )

    except Exception:
        filas = None

    if edad_horas <= 24:
        estado = "ACTUAL"

    elif edad_horas <= 72:
        estado = "ANTIGUO"

    else:
        estado = "OBSOLETO"

    return {
        "componente": componente.nombre,
        "critico": componente.critico,
        "existe": True,
        "tamano_kb": stat.st_size / 1024.0,
        "filas": filas,
        "modificado": modificacion.isoformat(
            timespec="seconds"
        ),
        "edad_horas": edad_horas,
        "estado": estado,
        "ruta": str(ruta),
    }


def comprobar_sistema() -> tuple[
    bool,
    pd.DataFrame,
]:
    """Comprueba todos los componentes principales."""

    resultados = [
        analizar_componente(
            componente
        )
        for componente in COMPONENTES
    ]

    tabla = pd.DataFrame(
        resultados
    )

    errores_criticos = tabla[
        (tabla["critico"])
        & (~tabla["existe"])
    ]

    correcto = errores_criticos.empty

    return (
        correcto,
        tabla,
    )


def imprimir_resultado(
    tabla: pd.DataFrame,
) -> None:
    """Muestra diagnóstico en terminal."""

    salida = tabla[
        [
            "componente",
            "critico",
            "existe",
            "estado",
            "filas",
            "edad_horas",
        ]
    ].copy()

    print()

    print(
        "=" * 100
    )

    print(
        "COMPROBACIÓN KRONOS RELEASE V1"
    )

    print(
        "=" * 100
    )

    print(
        salida.to_string(
            index=False,
            float_format=lambda valor: (
                f"{valor:,.2f}"
            ),
        )
    )


def guardar_resultado(
    tabla: pd.DataFrame,
) -> Path:
    """Guarda diagnóstico del sistema."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta = (
        RUTA_RESULTADOS
        / "estado_release_v1.csv"
    )

    tabla.to_csv(
        ruta,
        index=False,
    )

    return ruta


def main() -> None:
    """Ejecuta diagnóstico independiente."""

    correcto, tabla = comprobar_sistema()

    imprimir_resultado(
        tabla
    )

    ruta = guardar_resultado(
        tabla
    )

    print()

    print(
        f"Resultado guardado: {ruta}"
    )

    print()

    if correcto:
        print(
            "ESTADO: SISTEMA OPERATIVO"
        )

    else:
        print(
            "ESTADO: SISTEMA INCOMPLETO"
        )

    raise SystemExit(
        0
        if correcto
        else 1
    )


if __name__ == "__main__":
    main()