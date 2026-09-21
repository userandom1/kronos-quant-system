from pathlib import Path
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch


# =============================================================================
# RUTAS
# =============================================================================

RUTA_BASE = Path(__file__).resolve().parents[1]

# Añadimos la raíz del repositorio para importar Kronos.
sys.path.insert(0, str(RUTA_BASE))

from model import Kronos, KronosPredictor, KronosTokenizer


RUTA_DATOS = (
    RUTA_BASE
    / "data"
    / "QQQ_diario.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "v3_qqq"
)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

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

VENTANA_MOMENTUM = 20

VENTANA_SMA = 20

PERIODO_PENDIENTE_SMA = 10


MODELOS = [
    "Kronos",
    "Naive",
    "Drift",
    "Momentum20",
    "SMA20",
]


# =============================================================================
# REPRODUCIBILIDAD
# =============================================================================


def configurar_semillas(
    semilla: int,
) -> None:
    """Configura las semillas pseudoaleatorias."""

    random.seed(
        semilla
    )

    np.random.seed(
        semilla
    )

    torch.manual_seed(
        semilla
    )

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(
            semilla
        )


# =============================================================================
# DATOS
# =============================================================================


def cargar_datos() -> pd.DataFrame:
    """Carga y valida el histórico diario de QQQ."""

    datos = pd.read_csv(
        RUTA_DATOS
    )

    datos["timestamps"] = pd.to_datetime(
        datos["timestamps"]
    )

    columnas = [
        "timestamps",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    faltantes = [
        columna
        for columna in columnas
        if columna not in datos.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas: {faltantes}"
        )

    datos = (
        datos[columnas]
        .dropna()
        .sort_values("timestamps")
        .reset_index(drop=True)
    )

    minimo = (
        LOOKBACK
        + HORIZONTE_MAXIMO
    )

    if len(datos) < minimo:
        raise ValueError(
            "No existen suficientes datos."
        )

    return datos


# =============================================================================
# KRONOS
# =============================================================================


def cargar_kronos() -> KronosPredictor:
    """Carga Kronos-base y su tokenizer."""

    print(
        "Cargando Kronos-Tokenizer-base..."
    )

    tokenizer = (
        KronosTokenizer.from_pretrained(
            "NeoQuasar/Kronos-Tokenizer-base"
        )
    )

    print(
        "Cargando Kronos-base..."
    )

    modelo = Kronos.from_pretrained(
        "NeoQuasar/Kronos-base"
    )

    predictor = KronosPredictor(
        modelo,
        tokenizer,
        max_context=512,
    )

    return predictor


# =============================================================================
# BENCHMARKS
# =============================================================================


def forecast_naive(
    contexto: pd.DataFrame,
) -> np.ndarray:
    """Random Walk sin drift: el precio esperado no cambia."""

    precio_actual = float(
        contexto["close"].iloc[-1]
    )

    return np.full(
        HORIZONTE_MAXIMO,
        precio_actual,
        dtype=float,
    )


def forecast_drift(
    contexto: pd.DataFrame,
) -> np.ndarray:
    """Proyecta el retorno logarítmico medio del contexto."""

    cierres = (
        contexto["close"]
        .astype(float)
        .to_numpy()
    )

    retornos_log = np.diff(
        np.log(cierres)
    )

    drift_diario = float(
        np.mean(retornos_log)
    )

    precio_actual = cierres[-1]

    pasos = np.arange(
        1,
        HORIZONTE_MAXIMO + 1,
    )

    return (
        precio_actual
        * np.exp(
            drift_diario * pasos
        )
    )


def forecast_momentum(
    contexto: pd.DataFrame,
) -> np.ndarray:
    """
    Proyecta el momentum medio observado
    durante las últimas sesiones.
    """

    cierres = (
        contexto["close"]
        .astype(float)
        .to_numpy()
    )

    muestra = cierres[
        -(VENTANA_MOMENTUM + 1):
    ]

    retornos_log = np.diff(
        np.log(muestra)
    )

    momentum_diario = float(
        np.mean(retornos_log)
    )

    precio_actual = cierres[-1]

    pasos = np.arange(
        1,
        HORIZONTE_MAXIMO + 1,
    )

    return (
        precio_actual
        * np.exp(
            momentum_diario * pasos
        )
    )


def forecast_sma(
    contexto: pd.DataFrame,
) -> np.ndarray:
    """
    Proyecta la pendiente reciente de la SMA20
    desde el precio de cierre actual.
    """

    cierres = (
        contexto["close"]
        .astype(float)
    )

    sma = (
        cierres
        .rolling(VENTANA_SMA)
        .mean()
        .dropna()
    )

    ultimas_sma = sma.iloc[
        -PERIODO_PENDIENTE_SMA:
    ].to_numpy()

    x = np.arange(
        len(ultimas_sma),
        dtype=float,
    )

    pendiente = float(
        np.polyfit(
            x,
            ultimas_sma,
            1,
        )[0]
    )

    precio_actual = float(
        cierres.iloc[-1]
    )

    pasos = np.arange(
        1,
        HORIZONTE_MAXIMO + 1,
    )

    prediccion = (
        precio_actual
        + pendiente * pasos
    )

    return prediccion


# =============================================================================
# MÉTRICAS
# =============================================================================


def calcular_max_drawdown(
    retornos: np.ndarray,
) -> float:
    """Calcula el máximo drawdown de una serie de retornos."""

    curva = np.cumprod(
        1.0 + retornos
    )

    maximo = np.maximum.accumulate(
        curva
    )

    drawdown = (
        curva / maximo
        - 1.0
    )

    return float(
        np.min(drawdown)
    )


def calcular_profit_factor(
    retornos: np.ndarray,
) -> float:
    """Calcula Profit Factor."""

    ganancias = retornos[
        retornos > 0
    ].sum()

    perdidas = np.abs(
        retornos[
            retornos < 0
        ].sum()
    )

    if perdidas == 0:
        return float("nan")

    return float(
        ganancias / perdidas
    )


def calcular_r2(
    real: np.ndarray,
    predicho: np.ndarray,
) -> float:
    """Calcula R² sobre retornos."""

    ss_res = np.sum(
        np.square(
            real - predicho
        )
    )

    ss_tot = np.sum(
        np.square(
            real - np.mean(real)
        )
    )

    if ss_tot == 0:
        return float("nan")

    return float(
        1.0 - ss_res / ss_tot
    )


# =============================================================================
# WALK-FORWARD
# =============================================================================


def ejecutar_walk_forward(
    datos: pd.DataFrame,
    predictor: KronosPredictor,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta Kronos y los benchmarks ventana a ventana."""

    resultados_finales: list[dict] = []

    resultados_puntos: list[dict] = []

    columnas_kronos = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    origenes = list(
        range(
            LOOKBACK,
            len(datos)
            - HORIZONTE_MAXIMO
            + 1,
            PASO_VENTANA,
        )
    )

    total = len(origenes)

    print()
    print("=" * 90)
    print("V3 WALK-FORWARD: KRONOS VS BENCHMARKS")
    print("=" * 90)
    print(
        f"Ventanas: {total}"
    )
    print(
        f"Contexto: {LOOKBACK}"
    )
    print(
        f"Paso: {PASO_VENTANA}"
    )
    print(
        f"Horizonte máximo: {HORIZONTE_MAXIMO}"
    )
    print()

    for numero, origen in enumerate(
        origenes,
        start=1,
    ):
        inicio = (
            origen - LOOKBACK
        )

        fin = (
            origen + HORIZONTE_MAXIMO
        )

        contexto = datos.iloc[
            inicio:origen
        ].copy()

        futuro = datos.iloc[
            origen:fin
        ].copy()

        futuro = futuro.reset_index(
            drop=True
        )

        fecha_origen = contexto[
            "timestamps"
        ].iloc[-1]

        precio_origen = float(
            contexto[
                "close"
            ].iloc[-1]
        )

        print(
            f"[{numero:02d}/{total:02d}] "
            f"{fecha_origen.date()}"
        )

        # ---------------------------------------------------------------------
        # Kronos
        # ---------------------------------------------------------------------

        pred_kronos = predictor.predict(
            df=contexto[
                columnas_kronos
            ].copy(),
            x_timestamp=contexto[
                "timestamps"
            ].copy(),
            y_timestamp=futuro[
                "timestamps"
            ].copy(),
            pred_len=HORIZONTE_MAXIMO,
            T=TEMPERATURA,
            top_p=TOP_P,
            sample_count=SAMPLE_COUNT,
            verbose=False,
        )

        pred_kronos = (
            pred_kronos[
                "close"
            ]
            .reset_index(drop=True)
            .astype(float)
            .to_numpy()
        )

        # ---------------------------------------------------------------------
        # Benchmarks
        # ---------------------------------------------------------------------

        forecasts = {
            "Kronos": pred_kronos,
            "Naive": forecast_naive(
                contexto
            ),
            "Drift": forecast_drift(
                contexto
            ),
            "Momentum20": forecast_momentum(
                contexto
            ),
            "SMA20": forecast_sma(
                contexto
            ),
        }

        # ---------------------------------------------------------------------
        # Predicciones punto a punto
        # ---------------------------------------------------------------------

        for modelo, prediccion in forecasts.items():
            for paso in range(
                HORIZONTE_MAXIMO
            ):
                resultados_puntos.append(
                    {
                        "ventana": numero,
                        "modelo": modelo,
                        "fecha_origen": fecha_origen,
                        "fecha_predicha": futuro[
                            "timestamps"
                        ].iloc[paso],
                        "paso": paso + 1,
                        "precio_origen": precio_origen,
                        "close_real": float(
                            futuro[
                                "close"
                            ].iloc[paso]
                        ),
                        "close_predicho": float(
                            prediccion[
                                paso
                            ]
                        ),
                    }
                )

        # ---------------------------------------------------------------------
        # Resultado final por horizonte
        # ---------------------------------------------------------------------

        for horizonte in HORIZONTES:
            precio_real = float(
                futuro[
                    "close"
                ].iloc[
                    horizonte - 1
                ]
            )

            retorno_real = (
                precio_real
                / precio_origen
                - 1.0
            )

            for modelo, prediccion in forecasts.items():
                precio_predicho = float(
                    prediccion[
                        horizonte - 1
                    ]
                )

                retorno_predicho = (
                    precio_predicho
                    / precio_origen
                    - 1.0
                )

                direccion_real = int(
                    np.sign(
                        retorno_real
                    )
                )

                direccion_predicha = int(
                    np.sign(
                        retorno_predicho
                    )
                )

                acierto = int(
                    direccion_real
                    == direccion_predicha
                )

                retorno_estrategia = (
                    direccion_predicha
                    * retorno_real
                )

                resultados_finales.append(
                    {
                        "ventana": numero,
                        "modelo": modelo,
                        "fecha_origen": fecha_origen,
                        "horizonte": horizonte,
                        "precio_origen": precio_origen,
                        "precio_real": precio_real,
                        "precio_predicho": precio_predicho,
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
                        "acierto_direccion": acierto,
                        "retorno_estrategia": (
                            retorno_estrategia
                        ),
                    }
                )

    return (
        pd.DataFrame(
            resultados_finales
        ),
        pd.DataFrame(
            resultados_puntos
        ),
    )


# =============================================================================
# RESUMEN DE MÉTRICAS
# =============================================================================


def generar_resumen(
    resultados: pd.DataFrame,
    puntos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula las métricas de todos los modelos."""

    resumen: list[dict] = []

    for horizonte in HORIZONTES:
        for modelo in MODELOS:
            finales = resultados[
                (
                    resultados["modelo"]
                    == modelo
                )
                & (
                    resultados["horizonte"]
                    == horizonte
                )
            ].copy()

            detalle = puntos[
                (
                    puntos["modelo"]
                    == modelo
                )
                & (
                    puntos["paso"]
                    <= horizonte
                )
            ].copy()

            real_precio = detalle[
                "close_real"
            ].to_numpy()

            pred_precio = detalle[
                "close_predicho"
            ].to_numpy()

            error_precio = (
                pred_precio
                - real_precio
            )

            mae_precio = np.mean(
                np.abs(
                    error_precio
                )
            )

            rmse_precio = np.sqrt(
                np.mean(
                    np.square(
                        error_precio
                    )
                )
            )

            mape = (
                np.mean(
                    np.abs(
                        error_precio
                        / real_precio
                    )
                )
                * 100.0
            )

            bias = np.mean(
                error_precio
            )

            retorno_real = finales[
                "retorno_real"
            ].to_numpy()

            retorno_predicho = finales[
                "retorno_predicho"
            ].to_numpy()

            error_retorno = (
                retorno_predicho
                - retorno_real
            )

            mae_retorno = (
                np.mean(
                    np.abs(
                        error_retorno
                    )
                )
                * 100.0
            )

            rmse_retorno = (
                np.sqrt(
                    np.mean(
                        np.square(
                            error_retorno
                        )
                    )
                )
                * 100.0
            )

            directional_accuracy = (
                finales[
                    "acierto_direccion"
                ].mean()
                * 100.0
            )

            if (
                np.std(
                    retorno_real
                )
                == 0
                or np.std(
                    retorno_predicho
                )
                == 0
            ):
                correlacion = float(
                    "nan"
                )

            else:
                correlacion = float(
                    np.corrcoef(
                        retorno_real,
                        retorno_predicho,
                    )[0, 1]
                )

            r2 = calcular_r2(
                retorno_real,
                retorno_predicho,
            )

            retornos_estrategia = finales[
                "retorno_estrategia"
            ].to_numpy()

            desviacion_estrategia = np.std(
                retornos_estrategia,
                ddof=1,
            )

            if desviacion_estrategia == 0:
                sharpe = float(
                    "nan"
                )

            else:
                # Las ventanas avanzan PASO_VENTANA sesiones.
                factor_anualizacion = np.sqrt(
                    252.0
                    / PASO_VENTANA
                )

                sharpe = (
                    np.mean(
                        retornos_estrategia
                    )
                    / desviacion_estrategia
                    * factor_anualizacion
                )

            win_rate = (
                np.mean(
                    retornos_estrategia > 0
                )
                * 100.0
            )

            profit_factor = (
                calcular_profit_factor(
                    retornos_estrategia
                )
            )

            max_drawdown = (
                calcular_max_drawdown(
                    retornos_estrategia
                )
                * 100.0
            )

            resumen.append(
                {
                    "modelo": modelo,
                    "horizonte": horizonte,
                    "ventanas": len(
                        finales
                    ),
                    "mae_precio": mae_precio,
                    "rmse_precio": rmse_precio,
                    "mape_precio_pct": mape,
                    "bias_precio": bias,
                    "mae_retorno_pct": mae_retorno,
                    "rmse_retorno_pct": rmse_retorno,
                    "directional_accuracy_pct": (
                        directional_accuracy
                    ),
                    "information_coefficient": (
                        correlacion
                    ),
                    "r2_retornos": r2,
                    "sharpe_senal": sharpe,
                    "win_rate_pct": win_rate,
                    "profit_factor": (
                        profit_factor
                    ),
                    "max_drawdown_pct": (
                        max_drawdown
                    ),
                }
            )

    return pd.DataFrame(
        resumen
    )


# =============================================================================
# GRÁFICOS
# =============================================================================


def grafico_directional_accuracy(
    resumen: pd.DataFrame,
) -> None:
    """Compara el acierto direccional."""

    pivot = resumen.pivot(
        index="horizonte",
        columns="modelo",
        values="directional_accuracy_pct",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(12, 6),
    )

    ax.axhline(
        50.0,
        linestyle="--",
        linewidth=1,
        label="Referencia 50 %",
    )

    ax.set_title(
        "QQQ - Acierto direccional por modelo"
    )

    ax.set_xlabel(
        "Horizonte (sesiones)"
    )

    ax.set_ylabel(
        "Directional Accuracy (%)"
    )

    ax.legend()

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "01_directional_accuracy.png",
        dpi=180,
    )

    plt.close()


def grafico_rmse_retorno(
    resumen: pd.DataFrame,
) -> None:
    """Compara RMSE de retornos."""

    pivot = resumen.pivot(
        index="horizonte",
        columns="modelo",
        values="rmse_retorno_pct",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(12, 6),
    )

    ax.set_title(
        "QQQ - RMSE de retorno por modelo"
    )

    ax.set_xlabel(
        "Horizonte (sesiones)"
    )

    ax.set_ylabel(
        "RMSE retorno (%)"
    )

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "02_rmse_retorno.png",
        dpi=180,
    )

    plt.close()


def grafico_information_coefficient(
    resumen: pd.DataFrame,
) -> None:
    """Compara correlación retorno real/predicho."""

    pivot = resumen.pivot(
        index="horizonte",
        columns="modelo",
        values="information_coefficient",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(12, 6),
    )

    ax.axhline(
        0.0,
        linewidth=1,
    )

    ax.set_title(
        "QQQ - Information Coefficient"
    )

    ax.set_xlabel(
        "Horizonte (sesiones)"
    )

    ax.set_ylabel(
        "Correlación"
    )

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "03_information_coefficient.png",
        dpi=180,
    )

    plt.close()


def grafico_sharpe(
    resumen: pd.DataFrame,
) -> None:
    """Compara Sharpe exploratorio de las señales."""

    pivot = resumen.pivot(
        index="horizonte",
        columns="modelo",
        values="sharpe_senal",
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(12, 6),
    )

    ax.axhline(
        0.0,
        linewidth=1,
    )

    ax.set_title(
        "QQQ - Sharpe de señal"
    )

    ax.set_xlabel(
        "Horizonte (sesiones)"
    )

    ax.set_ylabel(
        "Sharpe anualizado"
    )

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "04_sharpe_senal.png",
        dpi=180,
    )

    plt.close()


def grafico_curvas_20(
    resultados: pd.DataFrame,
) -> None:
    """Compara las curvas acumuladas a 20 sesiones."""

    datos = resultados[
        resultados[
            "horizonte"
        ]
        == 20
    ].copy()

    plt.figure(
        figsize=(13, 7)
    )

    for modelo in MODELOS:
        modelo_df = datos[
            datos["modelo"]
            == modelo
        ].sort_values(
            "fecha_origen"
        )

        curva = (
            1.0
            + modelo_df[
                "retorno_estrategia"
            ]
        ).cumprod()

        plt.plot(
            modelo_df[
                "fecha_origen"
            ],
            curva,
            label=modelo,
        )

    plt.axhline(
        1.0,
        linewidth=1,
    )

    plt.title(
        "QQQ - Curva acumulada de señal - Horizonte 20 sesiones"
    )

    plt.xlabel(
        "Fecha"
    )

    plt.ylabel(
        "Capital normalizado"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "05_curva_senales_h20.png",
        dpi=180,
    )

    plt.close()


# =============================================================================
# RANKING
# =============================================================================


def crear_ranking(
    resumen: pd.DataFrame,
) -> pd.DataFrame:
    """
    Genera una tabla sencilla de ranking.

    No debe interpretarse como una función objetivo
    definitiva para trading.
    """

    ranking = resumen.copy()

    ranking[
        "rank_directional"
    ] = ranking.groupby(
        "horizonte"
    )[
        "directional_accuracy_pct"
    ].rank(
        ascending=False,
        method="min",
    )

    ranking[
        "rank_rmse"
    ] = ranking.groupby(
        "horizonte"
    )[
        "rmse_retorno_pct"
    ].rank(
        ascending=True,
        method="min",
    )

    ranking[
        "rank_ic"
    ] = ranking.groupby(
        "horizonte"
    )[
        "information_coefficient"
    ].rank(
        ascending=False,
        method="min",
    )

    ranking[
        "rank_sharpe"
    ] = ranking.groupby(
        "horizonte"
    )[
        "sharpe_senal"
    ].rank(
        ascending=False,
        method="min",
    )

    ranking[
        "puntuacion_media"
    ] = ranking[
        [
            "rank_directional",
            "rank_rmse",
            "rank_ic",
            "rank_sharpe",
        ]
    ].mean(
        axis=1
    )

    return ranking.sort_values(
        [
            "horizonte",
            "puntuacion_media",
        ]
    )


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Ejecuta la V3 completa."""

    configurar_semillas(
        SEMILLA
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_datos()

    print()
    print(
        f"Observaciones disponibles: {len(datos)}"
    )

    print(
        "Periodo:"
        f" {datos['timestamps'].iloc[0].date()}"
        " ->"
        f" {datos['timestamps'].iloc[-1].date()}"
    )

    print()
    print(
        f"Torch: {torch.__version__}"
    )

    print(
        f"CUDA disponible: {torch.cuda.is_available()}"
    )

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0),
        )

    predictor = cargar_kronos()

    (
        resultados,
        puntos,
    ) = ejecutar_walk_forward(
        datos,
        predictor,
    )

    resumen = generar_resumen(
        resultados,
        puntos,
    )

    ranking = crear_ranking(
        resumen
    )

    resultados.to_csv(
        RUTA_RESULTADOS
        / "resultados_por_ventana.csv",
        index=False,
    )

    puntos.to_csv(
        RUTA_RESULTADOS
        / "predicciones_punto_a_punto.csv",
        index=False,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "metricas_modelos.csv",
        index=False,
    )

    ranking.to_csv(
        RUTA_RESULTADOS
        / "ranking_modelos.csv",
        index=False,
    )

    grafico_directional_accuracy(
        resumen
    )

    grafico_rmse_retorno(
        resumen
    )

    grafico_information_coefficient(
        resumen
    )

    grafico_sharpe(
        resumen
    )

    grafico_curvas_20(
        resultados
    )

    print()
    print("=" * 120)
    print("MÉTRICAS V3")
    print("=" * 120)

    columnas_mostrar = [
        "modelo",
        "horizonte",
        "rmse_retorno_pct",
        "directional_accuracy_pct",
        "information_coefficient",
        "r2_retornos",
        "sharpe_senal",
        "max_drawdown_pct",
    ]

    print(
        resumen[
            columnas_mostrar
        ].to_string(
            index=False,
            float_format=lambda valor: (
                f"{valor:.4f}"
            ),
        )
    )

    print()
    print("=" * 120)
    print("RANKING")
    print("=" * 120)

    print(
        ranking[
            [
                "modelo",
                "horizonte",
                "puntuacion_media",
            ]
        ].to_string(
            index=False,
            float_format=lambda valor: (
                f"{valor:.2f}"
            ),
        )
    )

    print()
    print(
        "Resultados:"
    )

    print(
        RUTA_RESULTADOS
    )


if __name__ == "__main__":
    main()