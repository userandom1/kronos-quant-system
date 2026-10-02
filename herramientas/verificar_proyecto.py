"""Ejecuta la suite sin red, con temporales y cachés dentro del proyecto."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sin-modelos", action="store_true", help="Omite inferencia con pesos de Kronos")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    entorno = os.environ.copy()
    for variable, carpeta in {"TEMP": "tmp", "TMP": "tmp", "MPLCONFIGDIR": "matplotlib", "HF_HOME": "huggingface"}.items():
        ruta = raiz / ".cache" / carpeta
        ruta.mkdir(parents=True, exist_ok=True)
        entorno[variable] = str(ruta)
    entorno["HF_HUB_OFFLINE"] = "1"
    comando = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if args.sin_modelos:
        comando.extend(["-m", "not modelos"])
    raise SystemExit(subprocess.call(comando, cwd=raiz, env=entorno))


if __name__ == "__main__":
    main()
