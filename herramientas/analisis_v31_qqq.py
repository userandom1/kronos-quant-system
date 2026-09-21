from math import comb
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_V3 = (
    RUTA_BASE
    / "resultados"
    / "v3_qqq"
    / "resultados_por_ventana.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "v31_qqq"
)

HORIZONTES = [
    5,
    10,
    20,
]

BOOTSTRAP_REPETICIONES = 5000

SEMILLA = 42


# =============================================================================
# DATOS
# =============================================================================


def cargar_resultados_v3() -> pd.DataFrame:
    """Carga los resultados generados previamente por la V3."""

    if not RUTA_V3.exists():
        raise FileNotFoundError(
            f"No se encuentra el archivo V3: {RUTA_V3}"
        )

    datos = pd.read_csv(
        RUTA_V3,
        parse_dates=["fecha_origen"],
    )

    columnas_requeridas = [
        "ventana",
        "modelo",
        "fecha_origen",
        "horizonte",
        "precio_origen",
        "precio_real",
        "precio_predicho",
        "retorno_real",
        "retorno_predicho",
        "direccion_real",
        "direccion_predicha",
        "acierto_direccion",
        "retorno_estrategia",
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

    return datos


# =============================================================================
# BENCHMARKS DIRECCIONALES
# =============================================================================


def crear_benchmarks_direccionales(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Añade Always Long y Always Short.

    Estos benchmarks representan señales direccionales,
    no modelos de predicción de retorno.
    """

    referencia = (
        datos[
            datos["modelo"] == "Kronos"
        ]
        .copy()
        .reset_index(drop=True)
    )

    filas: list[pd.DataFrame] = []

    for nombre, direccion in [
        ("AlwaysLong", 1),
        ("AlwaysShort", -1),
    ]:
        nuevo = referencia.copy()

        nuevo["modelo"] = nombre

        # No existe forecast numérico de precio o retorno.
        nuevo["precio_predicho"] = np.nan
        nuevo["retorno_predicho"] = np.nan

        nuevo["direccion_predicha"] = direccion

        nuevo["acierto_direccion"] = (
            nuevo["direccion_real"]
            == direccion
        ).astype(int)

        nuevo["retorno_estrategia"] = (
            direccion
            * nuevo["retorno_real"]
        )

        filas.append(
            nuevo
        )

    return pd.concat(
        [
            datos,
            *filas,
        ],
        ignore_index=True,
    )


# =============================================================================
# TEST BINOMIAL
# =============================================================================


def p_value_binomial_dos_colas(
    aciertos: int,
    intentos: int,
) -> float:
    """
    Calcula un p-value binomial exacto bilateral
    bajo H0: probabilidad de acierto = 0.5.
    """

    if intentos <= 0:
        return float("nan")

    probabilidades = np.array(
        [
            comb(intentos, k)
            * (0.5 ** intentos)
            for k in range(
                intentos + 1
            )
        ],
        dtype=float,
    )

    prob_observada = probabilidades[
        aciertos
    ]

    p_value = probabilidades[
        probabilidades
        <= prob_observada + 1e-15
    ].sum()

    return float(
        min(
            p_value,
            1.0,
        )
    )


# =============================================================================
# INFORMATION COEFFICIENT
# =============================================================================


def calcular_ic(
    real: np.ndarray,
    predicho: np.ndarray,
) -> float:
    """Calcula correlación de Pearson."""

    mascara = (
        np.isfinite(real)
        & np.isfinite(predicho)
    )

    real = real[
        mascara
    ]

    predicho = predicho[
        mascara
    ]

    if len(real) < 3:
        return float("nan")

    if (
        np.std(real) == 0
        or np.std(predicho) == 0
    ):
        return float("nan")

    return float(
        np.corrcoef(
            real,
            predicho,
        )[0, 1]
    )


def bootstrap_ic(
    real: np.ndarray,
    predicho: np.ndarray,
    repeticiones: int,
    semilla: int,
) -> tuple[float, float]:
    """Calcula intervalo bootstrap 95% del IC."""

    mascara = (
        np.isfinite(real)
        & np.isfinite(predicho)
    )

    real = real[
        mascara
    ]

    predicho = predicho[
        mascara
    ]

    n = len(real)

    if n < 5:
        return (
            float("nan"),
            float("nan"),
        )

    generador = np.random.default_rng(
        semilla
    )

    valores: list[float] = []

    for _ in range(
        repeticiones
    ):
        indices = generador.integers(
            0,
            n,
            size=n,
        )

        ic = calcular_ic(
            real[indices],
            predicho[indices],
        )

        if np.isfinite(ic):
            valores.append(
                ic
            )

    if not valores:
        return (
            float("nan"),
            float("nan"),
        )

    inferior = float(
        np.percentile(
            valores,
            2.5,
        )
    )

    superior = float(
        np.percentile(
            valores,
            97.5,
        )
    )

    return (
        inferior,
        superior,
    )


# =============================================================================
# MÉTRICAS DIRECCIONALES
# =============================================================================


def calcular_resumen(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas estadísticas por modelo y horizonte."""

    filas: list[dict] = []

    modelos = datos[
        "modelo"
    ].unique()

    for horizonte in HORIZONTES:
        for modelo in modelos:
            muestra = datos[
                (
                    datos["modelo"]
                    == modelo
                )
                & (
                    datos["horizonte"]
                    == horizonte
                )
            ].copy()

            if muestra.empty:
                continue

            # -----------------------------------------------------------------
            # Cobertura
            # -----------------------------------------------------------------

            señales_activas = (
                muestra[
                    "direccion_predicha"
                ]
                != 0
            )

            cobertura = (
                señales_activas.mean()
                * 100.0
            )

            muestra_activa = muestra[
                señales_activas
            ]

            if len(
                muestra_activa
            ) > 0:
                aciertos = int(
                    muestra_activa[
                        "acierto_direccion"
                    ].sum()
                )

                intentos = len(
                    muestra_activa
                )

                directional_accuracy = (
                    aciertos
                    / intentos
                    * 100.0
                )

                p_value = (
                    p_value_binomial_dos_colas(
                        aciertos,
                        intentos,
                    )
                )

            else:
                aciertos = 0
                intentos = 0

                directional_accuracy = (
                    float("nan")
                )

                p_value = float(
                    "nan"
                )

            # -----------------------------------------------------------------
            # IC
            # -----------------------------------------------------------------

            real = muestra[
                "retorno_real"
            ].to_numpy(
                dtype=float
            )

            predicho = muestra[
                "retorno_predicho"
            ].to_numpy(
                dtype=float
            )

            ic = calcular_ic(
                real,
                predicho,
            )

            (
                ic_ci_inferior,
                ic_ci_superior,
            ) = bootstrap_ic(
                real,
                predicho,
                BOOTSTRAP_REPETICIONES,
                SEMILLA + horizonte,
            )

            # -----------------------------------------------------------------
            # Estrategia direccional
            # -----------------------------------------------------------------

            retornos_estrategia = muestra[
                "retorno_estrategia"
            ].to_numpy(
                dtype=float
            )

            retorno_medio = (
                np.mean(
                    retornos_estrategia
                )
                * 100.0
            )

            retorno_mediano = (
                np.median(
                    retornos_estrategia
                )
                * 100.0
            )

            filas.append(
                {
                    "modelo": modelo,
                    "horizonte": horizonte,
                    "observaciones": len(
                        muestra
                    ),
                    "senales_activas": intentos,
                    "cobertura_pct": cobertura,
                    "aciertos": aciertos,
                    "directional_accuracy_pct": (
                        directional_accuracy
                    ),
                    "p_value_binomial": p_value,
                    "information_coefficient": ic,
                    "ic_ci_95_inferior": (
                        ic_ci_inferior
                    ),
                    "ic_ci_95_superior": (
                        ic_ci_superior
                    ),
                    "retorno_estrategia_medio_pct": (
                        retorno_medio
                    ),
                    "retorno_estrategia_mediano_pct": (
                        retorno_mediano
                    ),
                }
            )

    return pd.DataFrame(
        filas
    )


# =============================================================================
# Z-SCORE KRONOS
# =============================================================================


def calcular_zscore_expanding(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula Z-score utilizando exclusivamente
    forecasts anteriores al actual.

    Evita usar información futura para estandarizar
    la señal.
    """

    kronos = (
        datos[
            datos["modelo"]
            == "Kronos"
        ]
        .copy()
        .sort_values(
            [
                "horizonte",
                "fecha_origen",
            ]
        )
    )

    resultados: list[pd.DataFrame] = []

    for horizonte in HORIZONTES:
        muestra = kronos[
            kronos["horizonte"]
            == horizonte
        ].copy()

        serie = muestra[
            "retorno_predicho"
        ]

        media_previa = (
            serie
            .expanding(
                min_periods=10
            )
            .mean()
            .shift(1)
        )

        desviacion_previa = (
            serie
            .expanding(
                min_periods=10
            )
            .std(
                ddof=1
            )
            .shift(1)
        )

        muestra[
            "media_prediccion_previa"
        ] = media_previa

        muestra[
            "desviacion_prediccion_previa"
        ] = desviacion_previa

        muestra[
            "zscore_kronos"
        ] = (
            (
                muestra[
                    "retorno_predicho"
                ]
                - media_previa
            )
            / desviacion_previa
        )

        muestra[
            "regimen_kronos"
        ] = pd.cut(
            muestra[
                "zscore_kronos"
            ],
            bins=[
                -np.inf,
                -1.0,
                -0.5,
                0.5,
                1.0,
                np.inf,
            ],
            labels=[
                "Bajista fuerte",
                "Bajista",
                "Neutral",
                "Alcista",
                "Alcista fuerte",
            ],
        )

        resultados.append(
            muestra
        )

    return pd.concat(
        resultados,
        ignore_index=True,
    )


# =============================================================================
# QUINTILES
# =============================================================================


def analizar_quintiles(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Analiza retorno real según quintil del forecast Kronos."""

    kronos = datos[
        datos["modelo"]
        == "Kronos"
    ].copy()

    resultados: list[dict] = []

    for horizonte in HORIZONTES:
        muestra = kronos[
            kronos["horizonte"]
            == horizonte
        ].copy()

        muestra = muestra.sort_values(
            "retorno_predicho"
        )

        muestra[
            "quintil"
        ] = pd.qcut(
            muestra[
                "retorno_predicho"
            ],
            q=5,
            labels=[
                "Q1",
                "Q2",
                "Q3",
                "Q4",
                "Q5",
            ],
        )

        agrupado = muestra.groupby(
            "quintil",
            observed=True,
        )

        for quintil, grupo in agrupado:
            resultados.append(
                {
                    "horizonte": horizonte,
                    "quintil": quintil,
                    "observaciones": len(
                        grupo
                    ),
                    "forecast_kronos_medio_pct": (
                        grupo[
                            "retorno_predicho"
                        ].mean()
                        * 100.0
                    ),
                    "retorno_real_medio_pct": (
                        grupo[
                            "retorno_real"
                        ].mean()
                        * 100.0
                    ),
                    "retorno_real_mediano_pct": (
                        grupo[
                            "retorno_real"
                        ].median()
                        * 100.0
                    ),
                    "probabilidad_retorno_positivo_pct": (
                        (
                            grupo[
                                "retorno_real"
                            ]
                            > 0
                        ).mean()
                        * 100.0
                    ),
                }
            )

    return pd.DataFrame(
        resultados
    )


# =============================================================================
# GRÁFICOS
# =============================================================================


def grafico_quintiles(
    quintiles: pd.DataFrame,
) -> None:
    """Genera gráfico de retorno real por quintil."""

    for horizonte in HORIZONTES:
        muestra = quintiles[
            quintiles[
                "horizonte"
            ]
            == horizonte
        ]

        plt.figure(
            figsize=(9, 5)
        )

        plt.bar(
            muestra["quintil"],
            muestra[
                "retorno_real_medio_pct"
            ],
        )

        plt.axhline(
            0.0,
            linewidth=1,
        )

        plt.title(
            "Kronos-base - "
            f"Retorno real por quintil - {horizonte} sesiones"
        )

        plt.xlabel(
            "Quintil del forecast Kronos"
        )

        plt.ylabel(
            "Retorno real medio (%)"
        )

        plt.tight_layout()

        plt.savefig(
            RUTA_RESULTADOS
            / (
                f"quintiles_kronos_"
                f"{horizonte}d.png"
            ),
            dpi=180,
        )

        plt.close()


def grafico_ic(
    resumen: pd.DataFrame,
) -> None:
    """Muestra IC de Kronos con intervalo bootstrap."""

    muestra = resumen[
        resumen["modelo"]
        == "Kronos"
    ].copy()

    x = np.arange(
        len(muestra)
    )

    ic = muestra[
        "information_coefficient"
    ].to_numpy()

    inferior = (
        ic
        - muestra[
            "ic_ci_95_inferior"
        ].to_numpy()
    )

    superior = (
        muestra[
            "ic_ci_95_superior"
        ].to_numpy()
        - ic
    )

    plt.figure(
        figsize=(9, 5)
    )

    plt.errorbar(
        x,
        ic,
        yerr=[
            inferior,
            superior,
        ],
        fmt="o",
        capsize=6,
    )

    plt.axhline(
        0.0,
        linewidth=1,
    )

    plt.xticks(
        x,
        muestra[
            "horizonte"
        ].astype(str),
    )

    plt.xlabel(
        "Horizonte (sesiones)"
    )

    plt.ylabel(
        "Information Coefficient"
    )

    plt.title(
        "Kronos-base - IC con bootstrap 95%"
    )

    plt.tight_layout()

    plt.savefig(
        RUTA_RESULTADOS
        / "ic_bootstrap_kronos.png",
        dpi=180,
    )

    plt.close()


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Ejecuta la auditoría estadística V3.1."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_resultados_v3()

    datos_extendidos = (
        crear_benchmarks_direccionales(
            datos
        )
    )

    resumen = calcular_resumen(
        datos_extendidos
    )

    zscores = calcular_zscore_expanding(
        datos
    )

    quintiles = analizar_quintiles(
        datos
    )

    datos_extendidos.to_csv(
        RUTA_RESULTADOS
        / "resultados_extendidos.csv",
        index=False,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "resumen_estadistico.csv",
        index=False,
    )

    zscores.to_csv(
        RUTA_RESULTADOS
        / "kronos_zscore.csv",
        index=False,
    )

    quintiles.to_csv(
        RUTA_RESULTADOS
        / "kronos_quintiles.csv",
        index=False,
    )

    grafico_quintiles(
        quintiles
    )

    grafico_ic(
        resumen
    )

    print()
    print("=" * 125)
    print("V3.1 - AUDITORÍA ESTADÍSTICA")
    print("=" * 125)

    columnas = [
        "modelo",
        "horizonte",
        "cobertura_pct",
        "directional_accuracy_pct",
        "p_value_binomial",
        "information_coefficient",
        "ic_ci_95_inferior",
        "ic_ci_95_superior",
    ]

    print(
        resumen[
            columnas
        ].to_string(
            index=False,
            float_format=lambda x: (
                f"{x:.4f}"
            ),
        )
    )

    print()
    print("=" * 100)
    print("KRONOS - QUINTILES")
    print("=" * 100)

    print(
        quintiles.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:.4f}"
            ),
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