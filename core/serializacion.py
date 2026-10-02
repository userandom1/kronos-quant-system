"""Serialización segura de resultados científicos."""
from __future__ import annotations
import math
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

def serializar_json(
    valor: Any,
) -> Any:
    """Convierte estructuras internas a JSON seguro."""

    if valor is None:
        return None

    if isinstance(
        valor,
        (
            str,
            bool,
            int,
        ),
    ):
        return valor

    if isinstance(
        valor,
        float,
    ):
        if not math.isfinite(
            valor
        ):
            return None

        return valor

    if isinstance(
        valor,
        np.generic,
    ):
        return serializar_json(
            valor.item()
        )

    if isinstance(
        valor,
        np.ndarray,
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor.tolist()
        ]

    if isinstance(
        valor,
        (
            datetime,
            date,
            pd.Timestamp,
        ),
    ):
        return valor.isoformat()

    if isinstance(
        valor,
        Path,
    ):
        return str(
            valor
        )

    if isinstance(
        valor,
        pd.DataFrame,
    ):
        return [
            serializar_json(
                fila
            )
            for fila in valor.to_dict(
                orient="records"
            )
        ]

    if isinstance(
        valor,
        pd.Series,
    ):
        return {
            str(clave): serializar_json(
                dato
            )
            for clave, dato
            in valor.to_dict().items()
        }

    if isinstance(
        valor,
        pd.Index,
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor.tolist()
        ]

    if is_dataclass(
        valor
    ):
        return serializar_json(
            asdict(
                valor
            )
        )

    if isinstance(
        valor,
        dict,
    ):
        return {
            str(clave): serializar_json(
                dato
            )
            for clave, dato
            in valor.items()
        }

    if isinstance(
        valor,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            serializar_json(
                elemento
            )
            for elemento in valor
        ]

    if pd.isna(
        valor
    ):
        return None

    return str(
        valor
    )
