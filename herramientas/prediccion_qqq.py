from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

# Añade la raíz del repositorio para poder importar el módulo model de Kronos.
sys.path.insert(0, str(RUTA_BASE))

from model import Kronos, KronosPredictor, KronosTokenizer


RUTA_DATOS = RUTA_BASE / "data" / "QQQ_diario.csv"
RUTA_RESULTADOS = RUTA_BASE / "resultados"

LOOKBACK = 400
PRED_LEN = 120


def cargar_datos() -> pd.DataFrame:
    """Carga y valida los datos diarios de QQQ."""

    datos = pd.read_csv(RUTA_DATOS)

    datos["timestamps"] = pd.to_datetime(datos["timestamps"])

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

    if len(datos) < LOOKBACK + PRED_LEN:
        raise ValueError(
            "No existen suficientes filas para realizar la prueba."
        )

    return datos


def main() -> None:
    """Ejecuta una primera predicción histórica de QQQ con Kronos."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Cargando datos de QQQ...")
    datos = cargar_datos()

    print(f"Sesiones disponibles: {len(datos)}")

    # Usamos las primeras 520 sesiones para disponer
    # de 400 sesiones de contexto y 120 conocidas
    # con las que comparar la predicción.
    inicio = 0

    fin_contexto = inicio + LOOKBACK
    fin_prediccion = fin_contexto + PRED_LEN

    contexto = datos.iloc[
        inicio:fin_contexto
    ].copy()

    realidad = datos.iloc[
        fin_contexto:fin_prediccion
    ].copy()

    columnas_modelo = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    x_df = contexto[columnas_modelo]

    x_timestamp = contexto["timestamps"]

    y_timestamp = realidad["timestamps"]

    print()
    print("Periodo de contexto:")
    print(
        contexto["timestamps"].iloc[0],
        "->",
        contexto["timestamps"].iloc[-1],
    )

    print()
    print("Periodo que Kronos intentara predecir:")
    print(
        realidad["timestamps"].iloc[0],
        "->",
        realidad["timestamps"].iloc[-1],
    )

    print()
    print("Cargando Kronos-small...")

    tokenizer = KronosTokenizer.from_pretrained(
        "NeoQuasar/Kronos-Tokenizer-base"
    )

    modelo = Kronos.from_pretrained(
        "NeoQuasar/Kronos-small"
    )

    predictor = KronosPredictor(
        modelo,
        tokenizer,
        max_context=512,
    )

    print("Modelo cargado.")
    print()
    print("Ejecutando prediccion...")

    prediccion = predictor.predict(
        df=x_df,
        x_timestamp=x_timestamp,
        y_timestamp=y_timestamp,
        pred_len=PRED_LEN,
        T=1.0,
        top_p=0.9,
        sample_count=1,
        verbose=True,
    )

    prediccion = prediccion.reset_index(drop=True)

    resultado = pd.DataFrame(
        {
            "timestamps": realidad[
                "timestamps"
            ].reset_index(drop=True),
            "close_real": realidad[
                "close"
            ].reset_index(drop=True),
            "close_predicho": prediccion[
                "close"
            ].reset_index(drop=True),
        }
    )

    resultado["error"] = (
        resultado["close_predicho"]
        - resultado["close_real"]
    )

    resultado["error_absoluto"] = (
        resultado["error"].abs()
    )

    mae = resultado[
        "error_absoluto"
    ].mean()

    ruta_csv = (
        RUTA_RESULTADOS
        / "QQQ_prediccion_kronos.csv"
    )

    resultado.to_csv(
        ruta_csv,
        index=False,
    )

    print()
    print("=" * 70)
    print("RESULTADO")
    print("=" * 70)

    print(f"MAE precio cierre: {mae:.4f}")

    print()
    print(resultado.head(10))

    print()
    print(f"Resultado guardado en:")
    print(ruta_csv)

    plt.figure(figsize=(12, 6))

    plt.plot(
        resultado["timestamps"],
        resultado["close_real"],
        label="QQQ real",
    )

    plt.plot(
        resultado["timestamps"],
        resultado["close_predicho"],
        label="Kronos",
    )

    plt.xlabel("Fecha")
    plt.ylabel("Precio de cierre")
    plt.title(
        "QQQ - Kronos-small: prediccion vs realidad"
    )

    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()