from pathlib import Path
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch


RUTA_BASE = Path(__file__).resolve().parents[1]

# Añadimos la raíz del repositorio para importar Kronos.
sys.path.insert(0, str(RUTA_BASE))

from model import Kronos, KronosPredictor, KronosTokenizer


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

RUTA_DATOS = RUTA_BASE / "data" / "QQQ_diario.csv"

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "walk_forward_qqq"
)

LOOKBACK = 400

HORIZONTE_MAXIMO = 20

HORIZONTES = [
    5,
    10,
    20,
]

PASO_VENTANA = 20

SAMPLE_COUNT = 3

TEMPERATURA = 1.0

TOP_P = 0.9

SEMILLA = 42


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def configurar_semillas(semilla: int) -> None:
    """Configura semillas para mejorar la reproducibilidad."""

    random.seed(semilla)

    np.random.seed(semilla)

    torch.manual_seed(semilla)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(semilla)


def cargar_datos() -> pd.DataFrame:
    """Carga y valida el histórico de QQQ."""

    datos = pd.read_csv(
        RUTA_DATOS,
    )

    datos["timestamps"] = pd.to_datetime(
        datos["timestamps"],
    )

    columnas_requeridas = [
        "timestamps",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in datos.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {faltantes}"
        )

    datos = (
        datos[columnas_requeridas]
        .dropna()
        .reset_index(drop=True)
    )

    minimo_necesario = (
        LOOKBACK
        + HORIZONTE_MAXIMO
    )

    if len(datos) < minimo_necesario:
        raise ValueError(
            "No existen suficientes datos para realizar "
            "la evaluación walk-forward."
        )

    return datos


def cargar_modelo() -> KronosPredictor:
    """Carga tokenizer, modelo y predictor Kronos."""

    print("Cargando tokenizer...")

    tokenizer = KronosTokenizer.from_pretrained(
        "NeoQuasar/Kronos-Tokenizer-base"
    )

    print("Cargando Kronos-small...")

    modelo = Kronos.from_pretrained(
        "NeoQuasar/Kronos-small"
    )

    predictor = KronosPredictor(
        modelo,
        tokenizer,
        max_context=512,
    )

    return predictor


def calcular_metricas_precio(
    real: np.ndarray,
    predicho: np.ndarray,
) -> dict[str, float]:
    """Calcula métricas básicas sobre precios."""

    error = predicho - real

    mae = np.mean(
        np.abs(error)
    )

    rmse = np.sqrt(
        np.mean(
            np.square(error)
        )
    )

    mape = np.mean(
        np.abs(
            error / real
        )
    ) * 100.0

    bias = np.mean(
        error
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape_pct": float(mape),
        "bias": float(bias),
    }


# ---------------------------------------------------------------------------
# Walk-forward
# ---------------------------------------------------------------------------


def ejecutar_walk_forward(
    datos: pd.DataFrame,
    predictor: KronosPredictor,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta la evaluación walk-forward completa."""

    resultados_ventanas: list[dict] = []

    resultados_puntos: list[dict] = []

    columnas_modelo = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    origenes = list(
        range(
            LOOKBACK,
            len(datos) - HORIZONTE_MAXIMO + 1,
            PASO_VENTANA,
        )
    )

    total_ventanas = len(origenes)

    print()
    print("=" * 78)
    print("WALK-FORWARD QQQ")
    print("=" * 78)

    print(
        f"Ventanas que se evaluarán: "
        f"{total_ventanas}"
    )

    print(
        f"Contexto por ventana: "
        f"{LOOKBACK} sesiones"
    )

    print(
        f"Horizonte máximo: "
        f"{HORIZONTE_MAXIMO} sesiones"
    )

    print(
        f"Sample count: "
        f"{SAMPLE_COUNT}"
    )

    print()

    for numero_ventana, origen in enumerate(
        origenes,
        start=1,
    ):
        inicio_contexto = (
            origen - LOOKBACK
        )

        fin_futuro = (
            origen + HORIZONTE_MAXIMO
        )

        contexto = datos.iloc[
            inicio_contexto:origen
        ].copy()

        futuro_real = datos.iloc[
            origen:fin_futuro
        ].copy()

        precio_origen = float(
            contexto["close"].iloc[-1]
        )

        fecha_origen = contexto[
            "timestamps"
        ].iloc[-1]

        print(
            f"[{numero_ventana:02d}/"
            f"{total_ventanas:02d}] "
            f"Origen: "
            f"{fecha_origen.date()}"
        )

        x_df = contexto[
            columnas_modelo
        ].copy()

        x_timestamp = contexto[
            "timestamps"
        ].copy()

        y_timestamp = futuro_real[
            "timestamps"
        ].copy()

        prediccion = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=HORIZONTE_MAXIMO,
            T=TEMPERATURA,
            top_p=TOP_P,
            sample_count=SAMPLE_COUNT,
            verbose=False,
        )

        prediccion = (
            prediccion
            .reset_index(drop=True)
        )

        real_reset = (
            futuro_real
            .reset_index(drop=True)
        )

        for paso in range(
            HORIZONTE_MAXIMO
        ):
            resultados_puntos.append(
                {
                    "ventana": numero_ventana,
                    "fecha_origen": fecha_origen,
                    "fecha_predicha": real_reset[
                        "timestamps"
                    ].iloc[paso],
                    "paso": paso + 1,
                    "precio_origen": precio_origen,
                    "close_real": float(
                        real_reset[
                            "close"
                        ].iloc[paso]
                    ),
                    "close_predicho": float(
                        prediccion[
                            "close"
                        ].iloc[paso]
                    ),
                }
            )

        for horizonte in HORIZONTES:
            precio_real_final = float(
                real_reset[
                    "close"
                ].iloc[horizonte - 1]
            )

            precio_predicho_final = float(
                prediccion[
                    "close"
                ].iloc[horizonte - 1]
            )

            retorno_real = (
                precio_real_final
                / precio_origen
                - 1.0
            )

            retorno_predicho = (
                precio_predicho_final
                / precio_origen
                - 1.0
            )

            direccion_real = int(
                np.sign(retorno_real)
            )

            direccion_predicha = int(
                np.sign(retorno_predicho)
            )

            acierto_direccion = int(
                direccion_real
                == direccion_predicha
            )

            resultados_ventanas.append(
                {
                    "ventana": numero_ventana,
                    "fecha_origen": fecha_origen,
                    "horizonte": horizonte,
                    "precio_origen": precio_origen,
                    "precio_real_final": precio_real_final,
                    "precio_predicho_final": (
                        precio_predicho_final
                    ),
                    "retorno_real": retorno_real,
                    "retorno_predicho": retorno_predicho,
                    "error_retorno": (
                        retorno_predicho
                        - retorno_real
                    ),
                    "direccion_real": direccion_real,
                    "direccion_predicha": (
                        direccion_predicha
                    ),
                    "acierto_direccion": (
                        acierto_direccion
                    ),
                }
            )

    return (
        pd.DataFrame(resultados_ventanas),
        pd.DataFrame(resultados_puntos),
    )


# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------


def generar_resumen(
    resultados_ventanas: pd.DataFrame,
    resultados_puntos: pd.DataFrame,
) -> pd.DataFrame:
    """Genera métricas agregadas por horizonte."""

    filas_resumen: list[dict] = []

    for horizonte in HORIZONTES:
        ventanas = resultados_ventanas[
            resultados_ventanas[
                "horizonte"
            ]
            == horizonte
        ].copy()

        puntos = resultados_puntos[
            resultados_puntos[
                "paso"
            ]
            <= horizonte
        ].copy()

        metricas_precio = (
            calcular_metricas_precio(
                puntos[
                    "close_real"
                ].to_numpy(),
                puntos[
                    "close_predicho"
                ].to_numpy(),
            )
        )

        directional_accuracy = (
            ventanas[
                "acierto_direccion"
            ].mean()
            * 100.0
        )

        mae_retorno = (
            ventanas[
                "error_retorno"
            ]
            .abs()
            .mean()
            * 100.0
        )

        rmse_retorno = (
            np.sqrt(
                np.mean(
                    np.square(
                        ventanas[
                            "error_retorno"
                        ]
                    )
                )
            )
            * 100.0
        )

        correlacion = (
            ventanas[
                [
                    "retorno_real",
                    "retorno_predicho",
                ]
            ]
            .corr()
            .iloc[0, 1]
        )

        filas_resumen.append(
            {
                "horizonte_sesiones": horizonte,
                "ventanas": len(ventanas),
                "mae_precio": (
                    metricas_precio["mae"]
                ),
                "rmse_precio": (
                    metricas_precio["rmse"]
                ),
                "mape_precio_pct": (
                    metricas_precio[
                        "mape_pct"
                    ]
                ),
                "bias_precio": (
                    metricas_precio["bias"]
                ),
                "mae_retorno_pct": (
                    mae_retorno
                ),
                "rmse_retorno_pct": (
                    rmse_retorno
                ),
                "directional_accuracy_pct": (
                    directional_accuracy
                ),
                "correlacion_retornos": (
                    correlacion
                ),
            }
        )

    return pd.DataFrame(
        filas_resumen
    )


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------


def guardar_grafico_direccional(
    resumen: pd.DataFrame,
) -> None:
    """Guarda el gráfico de acierto direccional."""

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        resumen[
            "horizonte_sesiones"
        ].astype(str),
        resumen[
            "directional_accuracy_pct"
        ],
    )

    plt.axhline(
        50.0,
        linestyle="--",
        label="Referencia 50 %",
    )

    plt.xlabel(
        "Horizonte (sesiones)"
    )

    plt.ylabel(
        "Directional Accuracy (%)"
    )

    plt.title(
        "Kronos-small - QQQ - "
        "Acierto direccional"
    )

    plt.legend()

    plt.tight_layout()

    ruta = (
        RUTA_RESULTADOS
        / "directional_accuracy.png"
    )

    plt.savefig(
        ruta,
        dpi=150,
    )

    plt.close()


def guardar_grafico_retornos(
    resultados_ventanas: pd.DataFrame,
) -> None:
    """Guarda real vs predicho para cada horizonte."""

    for horizonte in HORIZONTES:
        datos_h = resultados_ventanas[
            resultados_ventanas[
                "horizonte"
            ]
            == horizonte
        ].copy()

        plt.figure(
            figsize=(11, 5)
        )

        plt.plot(
            datos_h["fecha_origen"],
            datos_h["retorno_real"] * 100.0,
            label="Retorno real",
        )

        plt.plot(
            datos_h["fecha_origen"],
            datos_h["retorno_predicho"] * 100.0,
            label="Retorno Kronos",
        )

        plt.axhline(
            0.0,
            linewidth=1,
        )

        plt.xlabel(
            "Fecha de origen"
        )

        plt.ylabel(
            "Retorno (%)"
        )

        plt.title(
            f"QQQ - Kronos-small - "
            f"Horizonte {horizonte} sesiones"
        )

        plt.legend()

        plt.tight_layout()

        ruta = (
            RUTA_RESULTADOS
            / (
                f"retornos_horizonte_"
                f"{horizonte}.png"
            )
        )

        plt.savefig(
            ruta,
            dpi=150,
        )

        plt.close()


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------


def main() -> None:
    """Ejecuta la evaluación completa."""

    configurar_semillas(
        SEMILLA
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_datos()

    print(
        f"Sesiones disponibles: "
        f"{len(datos)}"
    )

    print(
        f"Periodo: "
        f"{datos['timestamps'].iloc[0].date()} "
        f"-> "
        f"{datos['timestamps'].iloc[-1].date()}"
    )

    print()

    print(
        "CUDA disponible:",
        torch.cuda.is_available(),
    )

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0),
        )

    predictor = cargar_modelo()

    (
        resultados_ventanas,
        resultados_puntos,
    ) = ejecutar_walk_forward(
        datos,
        predictor,
    )

    resumen = generar_resumen(
        resultados_ventanas,
        resultados_puntos,
    )

    ruta_ventanas = (
        RUTA_RESULTADOS
        / "resultados_ventanas.csv"
    )

    ruta_puntos = (
        RUTA_RESULTADOS
        / "resultados_puntos.csv"
    )

    ruta_resumen = (
        RUTA_RESULTADOS
        / "resumen_metricas.csv"
    )

    resultados_ventanas.to_csv(
        ruta_ventanas,
        index=False,
    )

    resultados_puntos.to_csv(
        ruta_puntos,
        index=False,
    )

    resumen.to_csv(
        ruta_resumen,
        index=False,
    )

    guardar_grafico_direccional(
        resumen
    )

    guardar_grafico_retornos(
        resultados_ventanas
    )

    print()
    print("=" * 78)
    print("RESUMEN WALK-FORWARD")
    print("=" * 78)

    print(
        resumen.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print()
    print(
        "Resultados guardados en:"
    )

    print(
        RUTA_RESULTADOS
    )


if __name__ == "__main__":
    main()