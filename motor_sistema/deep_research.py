"""Entrada CLI de Deep Research."""
from __future__ import annotations
import argparse
from motor_mercado.deep_research_activo import ejecutar_deep_research_activo


def main() -> None:
    """Ejecuta investigación y devuelve código no cero si no está completa."""
    parser = argparse.ArgumentParser(description="Deep Research universal")
    parser.add_argument("ticker")
    parser.add_argument("horizonte", type=int, nargs="?", help="Sesiones; por defecto 5/20/60")
    parser.add_argument("--vencimientos", type=int, default=12)
    parser.add_argument("--dte-escenarios", type=int, default=35)
    parser.add_argument("--modelos", nargs="+", choices=["DRIFT", "MOMENTUM", "KRONOS"])
    args = parser.parse_args()
    resultado = ejecutar_deep_research_activo(
        args.ticker, args.horizonte, args.vencimientos, args.dte_escenarios, args.modelos
    )
    raise SystemExit({"OK": 0, "PARCIAL": 2, "ERROR": 1}[resultado["estado"]])


if __name__ == "__main__":
    main()
