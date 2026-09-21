from __future__ import annotations

import logging
import subprocess
import sys
import time

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

RUTA_LOGS = (
    RUTA_RESULTADOS
    / "logs"
)

RUTA_LOGS.mkdir(
    parents=True,
    exist_ok=True,
)


@dataclass(frozen=True)
class PasoSistema:
    """Representa una etapa del pipeline Kronos."""

    numero: int
    nombre: str
    modulo: str
    argumentos: tuple[str, ...] = ()
    critico: bool = True


PASOS = [
    PasoSistema(
        numero=1,
        nombre="Market Regime V1 - QQQ",
        modulo="motor_mercado.estudio_regimen_v1",
        argumentos=(
            "QQQ",
        ),
        critico=False,
    ),
    PasoSistema(
        numero=2,
        nombre="Comparador Multi-Activo",
        modulo="motor_mercado.comparador_multi_activo",
        critico=True,
    ),
    PasoSistema(
        numero=3,
        nombre="Market Regime V2",
        modulo="motor_mercado.ejecutar_regimen_mercado_v2",
        critico=True,
    ),
    PasoSistema(
        numero=4,
        nombre="Señales Oficiales V2",
        modulo="motor_mercado.senales_v2",
        critico=True,
    ),
    PasoSistema(
        numero=5,
        nombre="Portfolio Engine V1",
        modulo="motor_portfolio.ejecutar_portfolio_v1",
        critico=False,
    ),
    PasoSistema(
        numero=6,
        nombre="Portfolio Engine V2",
        modulo="motor_portfolio.ejecutar_portfolio_v2",
        critico=True,
    ),
    PasoSistema(
        numero=7,
        nombre="Risk Engine V1",
        modulo="motor_riesgo.ejecutar_risk_engine_v1",
        critico=True,
    ),
    PasoSistema(
        numero=8,
        nombre="Cadena Real QQQ",
        modulo="motor_opciones.cadena_real_qqq",
        critico=True,
    ),
    PasoSistema(
        numero=9,
        nombre="Limpieza Cadena QQQ",
        modulo="motor_opciones.limpieza_cadena",
        critico=True,
    ),
    PasoSistema(
        numero=10,
        nombre="Exposiciones Dealer",
        modulo="motor_opciones.exposiciones",
        critico=True,
    ),
    PasoSistema(
        numero=11,
        nombre="Niveles Dealer",
        modulo="motor_opciones.niveles_dealer",
        critico=False,
    ),
    PasoSistema(
        numero=12,
        nombre="Dealer Engine V3.1",
        modulo="motor_opciones.dealer_v31",
        critico=False,
    ),
    PasoSistema(
        numero=13,
        nombre="Options Flow V1",
        modulo="motor_opciones.options_flow_v1",
        critico=False,
    ),
    PasoSistema(
        numero=14,
        nombre="Monitor Flow Dinámico",
        modulo="motor_opciones.monitor_flow",
        critico=False,
    ),
    PasoSistema(
        numero=15,
        nombre="Options Flow V2",
        modulo="motor_opciones.ejecutar_options_flow_v2",
        critico=False,
    ),
    PasoSistema(
        numero=16,
        nombre="Dealer Engine V4",
        modulo="motor_opciones.ejecutar_dealer_v4",
        critico=False,
    ),
]


def configurar_logging() -> logging.Logger:
    """Configura el sistema central de logging."""

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    ruta_log = (
        RUTA_LOGS
        / f"actualizacion_{timestamp}.log"
    )

    logger = logging.getLogger(
        "kronos_sistema"
    )

    logger.setLevel(
        logging.INFO
    )

    logger.handlers.clear()

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler_archivo = logging.FileHandler(
        ruta_log,
        encoding="utf-8",
    )

    handler_archivo.setFormatter(
        formato
    )

    handler_terminal = logging.StreamHandler(
        sys.stdout
    )

    handler_terminal.setFormatter(
        formato
    )

    logger.addHandler(
        handler_archivo
    )

    logger.addHandler(
        handler_terminal
    )

    logger.info(
        "Log principal: %s",
        ruta_log,
    )

    return logger


def construir_comando(
    paso: PasoSistema,
) -> list[str]:
    """Construye el comando completo de cada módulo."""

    return [
        sys.executable,
        "-m",
        paso.modulo,
        *paso.argumentos,
    ]


def ejecutar_modulo(
    paso: PasoSistema,
    logger: logging.Logger,
) -> dict:
    """Ejecuta un módulo como subproceso independiente."""

    logger.info(
        "=" * 90
    )

    logger.info(
        "PASO %02d | %s",
        paso.numero,
        paso.nombre,
    )

    logger.info(
        "Módulo: %s",
        paso.modulo,
    )

    if paso.argumentos:
        logger.info(
            "Argumentos: %s",
            " ".join(
                paso.argumentos
            ),
        )

    comando = construir_comando(
        paso
    )

    logger.info(
        "Comando: %s",
        " ".join(
            comando
        ),
    )

    inicio = time.perf_counter()

    proceso = subprocess.run(
        comando,
        cwd=RUTA_BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    duracion = (
        time.perf_counter()
        - inicio
    )

    if proceso.stdout:
        logger.info(
            "\n%s",
            proceso.stdout.strip(),
        )

    if proceso.stderr:
        if proceso.returncode == 0:
            logger.info(
                "\n%s",
                proceso.stderr.strip(),
            )

        else:
            logger.error(
                "\n%s",
                proceso.stderr.strip(),
            )

    correcto = (
        proceso.returncode == 0
    )

    if correcto:
        logger.info(
            "OK | %.2f segundos",
            duracion,
        )

    else:
        logger.error(
            "ERROR código=%d | %.2f segundos",
            proceso.returncode,
            duracion,
        )

    return {
        "numero": paso.numero,
        "nombre": paso.nombre,
        "modulo": paso.modulo,
        "argumentos": " ".join(
            paso.argumentos
        ),
        "critico": paso.critico,
        "correcto": correcto,
        "codigo_salida": proceso.returncode,
        "duracion_segundos": duracion,
    }


def imprimir_resumen(
    resultados: list[dict],
    logger: logging.Logger,
) -> None:
    """Muestra el resumen final del pipeline."""

    logger.info(
        ""
    )

    logger.info(
        "=" * 90
    )

    logger.info(
        "RESUMEN ACTUALIZACIÓN KRONOS"
    )

    logger.info(
        "=" * 90
    )

    for resultado in resultados:
        estado = (
            "OK"
            if resultado[
                "correcto"
            ]
            else "ERROR"
        )

        criticidad = (
            "CRÍTICO"
            if resultado[
                "critico"
            ]
            else "OPCIONAL"
        )

        logger.info(
            "%02d | %-8s | %-8s | %7.2fs | %s",
            resultado[
                "numero"
            ],
            estado,
            criticidad,
            resultado[
                "duracion_segundos"
            ],
            resultado[
                "nombre"
            ],
        )


def guardar_estado_pipeline(
    resultados: list[dict],
) -> Path:
    """Guarda el último estado completo del pipeline."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta = (
        RUTA_RESULTADOS
        / "ultimo_pipeline.csv"
    )

    datos = pd.DataFrame(
        resultados
    )

    datos[
        "fecha_ejecucion"
    ] = datetime.now().isoformat(
        timespec="seconds"
    )

    datos.to_csv(
        ruta,
        index=False,
    )

    return ruta


def actualizar_todo() -> bool:
    """Ejecuta el pipeline completo de Kronos."""

    logger = configurar_logging()

    logger.info(
        ""
    )

    logger.info(
        "=" * 90
    )

    logger.info(
        "KRONOS QUANT SYSTEM"
    )

    logger.info(
        "PIPELINE DE ACTUALIZACIÓN V1"
    )

    logger.info(
        "=" * 90
    )

    logger.info(
        "Ruta base: %s",
        RUTA_BASE,
    )

    logger.info(
        "Python: %s",
        sys.executable,
    )

    resultados = []

    inicio_total = time.perf_counter()

    for paso in PASOS:
        resultado = ejecutar_modulo(
            paso,
            logger,
        )

        resultados.append(
            resultado
        )

        if (
            not resultado[
                "correcto"
            ]
            and paso.critico
        ):
            logger.error(
                "Ha fallado un componente crítico: %s",
                paso.nombre,
            )

            logger.error(
                "El pipeline continuará para obtener "
                "un diagnóstico completo."
            )

    duracion_total = (
        time.perf_counter()
        - inicio_total
    )

    imprimir_resumen(
        resultados,
        logger,
    )

    ruta_estado = guardar_estado_pipeline(
        resultados
    )

    logger.info(
        ""
    )

    logger.info(
        "Estado guardado en: %s",
        ruta_estado,
    )

    errores_criticos = [
        resultado
        for resultado
        in resultados
        if (
            resultado[
                "critico"
            ]
            and not resultado[
                "correcto"
            ]
        )
    ]

    errores_opcionales = [
        resultado
        for resultado
        in resultados
        if (
            not resultado[
                "critico"
            ]
            and not resultado[
                "correcto"
            ]
        )
    ]

    logger.info(
        "Duración total      : %.2f segundos",
        duracion_total,
    )

    logger.info(
        "Errores críticos   : %d",
        len(
            errores_criticos
        ),
    )

    logger.info(
        "Errores opcionales : %d",
        len(
            errores_opcionales
        ),
    )

    if errores_criticos:
        logger.error(
            "PIPELINE FINALIZADO CON ERRORES CRÍTICOS."
        )

        return False

    logger.info(
        "PIPELINE CRÍTICO COMPLETADO CORRECTAMENTE."
    )

    if errores_opcionales:
        logger.warning(
            "Existen componentes opcionales pendientes."
        )

    return True


def main() -> None:
    """Punto de entrada del actualizador."""

    correcto = actualizar_todo()

    raise SystemExit(
        0
        if correcto
        else 1
    )


if __name__ == "__main__":
    main()