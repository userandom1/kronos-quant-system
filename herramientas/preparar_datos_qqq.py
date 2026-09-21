from pathlib import Path

import pandas as pd
import yfinance as yf


TICKER = "QQQ"

RUTA_SALIDA = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "QQQ_diario.csv"
)


def descargar_datos() -> pd.DataFrame:
    """Descarga histórico diario de QQQ y lo adapta al formato de Kronos."""

    datos = yf.download(
        TICKER,
        period="5y",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if datos.empty:
        raise RuntimeError("Yahoo Finance no ha devuelto datos.")

    if isinstance(datos.columns, pd.MultiIndex):
        datos.columns = datos.columns.get_level_values(0)

    datos = datos.reset_index()

    datos = datos.rename(
        columns={
            "Date": "timestamps",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    columnas = [
        "timestamps",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    datos = datos[columnas].copy()

    datos["timestamps"] = pd.to_datetime(
        datos["timestamps"]
    )

    datos = datos.dropna().reset_index(drop=True)

    return datos


def main() -> None:
    """Genera el CSV preparado para Kronos."""

    datos = descargar_datos()

    RUTA_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos.to_csv(
        RUTA_SALIDA,
        index=False,
    )

    print(f"Archivo generado: {RUTA_SALIDA}")
    print(f"Filas disponibles: {len(datos)}")
    print()
    print(datos.tail())


if __name__ == "__main__":
    main()