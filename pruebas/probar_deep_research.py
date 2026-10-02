from __future__ import annotations

from motor_mercado.deep_research_activo import (
    ejecutar_deep_research_activo,
)


def main() -> None:
    """Prueba rápida del pipeline de deep research."""
    for ticker in ["SPY", "XLK", "QQQ"]:
        print(f"\nProbando {ticker}...")
        resultado = ejecutar_deep_research_activo(
            ticker=ticker,
            horizonte=20,
        )
        print(resultado["ticker"], "OK")
        print("Resultados:", resultado["ruta_resultados"])


if __name__ == "__main__":
    main()