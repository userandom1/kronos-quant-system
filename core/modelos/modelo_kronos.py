from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.activos.clases_activo import ClaseActivo
from core.activos.modelo_activo import Activo
from core.modelos.modelo_base import (
    ModeloForecast,
    ResultadoForecast,
)


RUTA_BASE = Path(__file__).resolve().parents[2]

RUTA_CACHE = (
    RUTA_BASE
    / ".cache"
    / "huggingface"
)


class ModeloKronos(ModeloForecast):
    """Adaptador universal para Kronos."""

    nombre = "KRONOS"

    def __init__(
        self,
        modelo_id: str = "NeoQuasar/Kronos-small",
        tokenizer_id: str = "NeoQuasar/Kronos-Tokenizer-base",
        lookback: int = 400,
        max_context: int = 512,
        temperatura: float = 1.0,
        top_p: float = 0.9,
        sample_count: int = 1,
    ) -> None:
        self.modelo_id = modelo_id
        self.tokenizer_id = tokenizer_id
        self.lookback = lookback
        self.max_context = max_context
        self.temperatura = temperatura
        self.top_p = top_p
        self.sample_count = sample_count

        self._predictor = None
        self._dispositivo: str | None = None

    def _cargar(self) -> None:
        """Carga Kronos una sola vez."""

        if self._predictor is not None:
            return

        import torch

        from model import (
            Kronos,
            KronosPredictor,
            KronosTokenizer,
        )

        RUTA_CACHE.mkdir(
            parents=True,
            exist_ok=True,
        )

        dispositivo = (
            "cuda:0"
            if torch.cuda.is_available()
            else "cpu"
        )

        tokenizer = (
            KronosTokenizer.from_pretrained(
                self.tokenizer_id,
                cache_dir=str(
                    RUTA_CACHE
                ),
            )
        )

        modelo = Kronos.from_pretrained(
            self.modelo_id,
            cache_dir=str(
                RUTA_CACHE
            ),
        )

        tokenizer.eval()
        modelo.eval()

        self._predictor = KronosPredictor(
            modelo,
            tokenizer,
            device=dispositivo,
            max_context=self.max_context,
        )

        self._dispositivo = dispositivo

    @staticmethod
    def _timestamps_futuros(
        activo: Activo,
        ultimo_timestamp: pd.Timestamp,
        horizonte: int,
    ) -> pd.Series:
        """Construye timestamps futuros diarios."""

        ultimo_timestamp = pd.Timestamp(
            ultimo_timestamp
        )

        if activo.clase == ClaseActivo.CRYPTO:
            indice = pd.date_range(
                start=(
                    ultimo_timestamp
                    + pd.Timedelta(
                        days=1
                    )
                ),
                periods=horizonte,
                freq="D",
            )

        else:
            indice = pd.bdate_range(
                start=(
                    ultimo_timestamp
                    + pd.offsets.BDay(1)
                ),
                periods=horizonte,
            )

        return pd.Series(
            indice,
            name="timestamps",
        )

    def predecir(
        self,
        activo: Activo,
        datos: pd.DataFrame,
        horizonte: int,
    ) -> ResultadoForecast:
        """Genera forecast con Kronos."""

        self._cargar()

        if self._predictor is None:
            raise RuntimeError(
                "Kronos no se ha podido cargar."
            )

        columnas = [
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
                f"Faltan columnas para Kronos: "
                f"{faltantes}"
            )

        contexto = (
            datos[
                columnas
            ]
            .dropna(
                subset=[
                    "open",
                    "high",
                    "low",
                    "close",
                ]
            )
            .tail(
                self.lookback
            )
            .copy()
        )

        if len(contexto) < 100:
            raise RuntimeError(
                f"Histórico insuficiente para "
                f"Kronos en {activo.simbolo}."
            )

        x_timestamp = pd.Series(
            pd.to_datetime(
                contexto.index
            ),
            name="timestamps",
        ).reset_index(
            drop=True
        )

        x_df = contexto.reset_index(
            drop=True
        )

        y_timestamp = (
            self._timestamps_futuros(
                activo=activo,
                ultimo_timestamp=(
                    contexto.index[-1]
                ),
                horizonte=horizonte,
            )
        )

        import torch

        with torch.no_grad():
            prediccion = (
                self._predictor.predict(
                    df=x_df,
                    x_timestamp=x_timestamp,
                    y_timestamp=y_timestamp,
                    pred_len=horizonte,
                    T=self.temperatura,
                    top_p=self.top_p,
                    sample_count=(
                        self.sample_count
                    ),
                    verbose=False,
                )
            )

        if (
            prediccion.empty
            or "close"
            not in prediccion.columns
        ):
            raise RuntimeError(
                "Kronos no devolvió una "
                "predicción de cierre válida."
            )

        precio_actual = float(
            contexto[
                "close"
            ].iloc[-1]
        )

        precio_estimado = float(
            prediccion[
                "close"
            ].iloc[-1]
        )

        retorno_estimado = (
            precio_estimado
            / precio_actual
            - 1.0
        )

        return ResultadoForecast(
            simbolo=activo.simbolo,
            modelo=self.nombre,
            horizonte=horizonte,
            precio_actual=precio_actual,
            precio_estimado=precio_estimado,
            retorno_estimado=float(
                retorno_estimado
            ),
            metadata={
                "modelo_id": self.modelo_id,
                "tokenizer_id": (
                    self.tokenizer_id
                ),
                "lookback": len(
                    contexto
                ),
                "dispositivo": (
                    self._dispositivo
                ),
            },
        )