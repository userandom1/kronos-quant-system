from pathlib import Path

import numpy as np
import pandas as pd

from motor_opciones.griegas import (
    ParametrosOpcion,
    gamma,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_ENTRADA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "cadena_filtrada.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "intradia_v3"
)


MULTIPLICADOR = 100.0

TIPO_INTERES = 0.04

DIVIDENDO = 0.01

RANGO_SPOT_PCT = 3.0

PASO_SPOT = 0.25


def cargar_cadena() -> pd.DataFrame:
    """Carga la cadena limpia."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    datos["dte"] = pd.to_numeric(
        datos["dte"],
        errors="coerce",
    )

    return datos.dropna(
        subset=[
            "spot",
            "strike",
            "dte",
            "openInterest",
            "impliedVolatility",
            "tipo",
            "vencimiento",
        ]
    )


def clasificar_dte(
    dte: float,
) -> str:
    """Clasifica un contrato por horizonte temporal."""

    if dte <= 0.75:
        return "0DTE"

    if dte <= 2.50:
        return "1-2 DTE"

    if dte <= 7.50:
        return "3-7 DTE"

    if dte <= 30.50:
        return "8-30 DTE"

    return ">30 DTE"


def signo_dealer(
    tipo: str,
) -> float:
    """Aplica la convención dealer proxy."""

    if tipo == "call":
        return -1.0

    return 1.0


def crear_eje_spot(
    spot_base: float,
) -> np.ndarray:
    """Crea una rejilla fina de precios del subyacente."""

    minimo = (
        spot_base
        * (
            1.0
            - RANGO_SPOT_PCT
            / 100.0
        )
    )

    maximo = (
        spot_base
        * (
            1.0
            + RANGO_SPOT_PCT
            / 100.0
        )
    )

    return np.arange(
        minimo,
        maximo + PASO_SPOT / 2.0,
        PASO_SPOT,
    )


def calcular_perfiles(
    datos: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Calcula GEX:

    - total
    - por banda DTE
    - por vencimiento exacto
    """

    spot_base = float(
        datos["spot"].iloc[0]
    )

    eje_spot = crear_eje_spot(
        spot_base
    )

    total_filas = []
    banda_filas = []
    vencimiento_filas = []

    bandas = (
        "0DTE",
        "1-2 DTE",
        "3-7 DTE",
        "8-30 DTE",
        ">30 DTE",
    )

    vencimientos = sorted(
        datos[
            "vencimiento"
        ].unique()
    )

    print()
    print("=" * 80)
    print("GAMMA PROFILE V3")
    print("=" * 80)

    print(
        f"Spot base     : {spot_base:.4f}"
    )

    print(
        f"Paso de precio: ${PASO_SPOT:.2f}"
    )

    print(
        f"Puntos        : {len(eje_spot)}"
    )

    print()

    for numero, spot_escenario in enumerate(
        eje_spot,
        start=1,
    ):
        total = 0.0

        por_banda = {
            banda: 0.0
            for banda in bandas
        }

        por_vencimiento = {
            vencimiento: 0.0
            for vencimiento in vencimientos
        }

        for fila in datos.itertuples():
            dte = float(
                fila.dte
            )

            if dte <= 0:
                continue

            oi = float(
                fila.openInterest
            )

            if oi <= 0:
                continue

            parametros = ParametrosOpcion(
                spot=float(
                    spot_escenario
                ),
                strike=float(
                    fila.strike
                ),
                tiempo=dte / 365.0,
                volatilidad=float(
                    fila.impliedVolatility
                ),
                tipo_interes=TIPO_INTERES,
                dividendo=DIVIDENDO,
                tipo=fila.tipo,
            )

            gex = (
                gamma(
                    parametros
                )
                * oi
                * MULTIPLICADOR
                * spot_escenario**2
                * 0.01
                * signo_dealer(
                    fila.tipo
                )
            )

            total += gex

            banda = clasificar_dte(
                dte
            )

            por_banda[
                banda
            ] += gex

            por_vencimiento[
                fila.vencimiento
            ] += gex

        total_filas.append(
            {
                "spot": spot_escenario,
                "net_gex_1pct": total,
            }
        )

        for banda, valor in por_banda.items():
            banda_filas.append(
                {
                    "spot": spot_escenario,
                    "banda_dte": banda,
                    "net_gex_1pct": valor,
                }
            )

        for vencimiento, valor in (
            por_vencimiento.items()
        ):
            vencimiento_filas.append(
                {
                    "spot": spot_escenario,
                    "vencimiento": vencimiento,
                    "net_gex_1pct": valor,
                }
            )

        if numero % 25 == 0:
            print(
                f"[{numero}/{len(eje_spot)}] "
                f"Spot {spot_escenario:.2f}"
            )

    return (
        pd.DataFrame(
            total_filas
        ),
        pd.DataFrame(
            banda_filas
        ),
        pd.DataFrame(
            vencimiento_filas
        ),
    )


def buscar_flips(
    datos: pd.DataFrame,
    columna_grupo: str | None = None,
) -> pd.DataFrame:
    """Busca cruces de GEX por cero mediante interpolación."""

    resultados = []

    if columna_grupo is None:
        grupos = [
            (
                "TOTAL",
                datos,
            )
        ]

    else:
        grupos = list(
            datos.groupby(
                columna_grupo
            )
        )

    for nombre_grupo, grupo in grupos:
        grupo = grupo.sort_values(
            "spot"
        )

        valores = grupo[
            [
                "spot",
                "net_gex_1pct",
            ]
        ].to_numpy()

        for i in range(
            len(valores) - 1
        ):
            spot_1 = float(
                valores[i, 0]
            )

            gex_1 = float(
                valores[i, 1]
            )

            spot_2 = float(
                valores[i + 1, 0]
            )

            gex_2 = float(
                valores[i + 1, 1]
            )

            if gex_1 == 0:
                flip = spot_1

            elif (
                np.sign(gex_1)
                != np.sign(gex_2)
            ):
                flip = (
                    spot_1
                    + (
                        -gex_1
                    )
                    * (
                        spot_2
                        - spot_1
                    )
                    / (
                        gex_2
                        - gex_1
                    )
                )

            else:
                continue

            resultados.append(
                {
                    "grupo": nombre_grupo,
                    "gamma_flip": flip,
                    "spot_inferior": spot_1,
                    "spot_superior": spot_2,
                }
            )

    return pd.DataFrame(
        resultados
    )


def main() -> None:
    """Calcula Gamma Flip total y segmentado."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_cadena()

    (
        perfil_total,
        perfil_bandas,
        perfil_vencimientos,
    ) = calcular_perfiles(
        datos
    )

    flips_total = buscar_flips(
        perfil_total
    )

    flips_bandas = buscar_flips(
        perfil_bandas,
        "banda_dte",
    )

    flips_vencimientos = buscar_flips(
        perfil_vencimientos,
        "vencimiento",
    )

    perfil_total.to_csv(
        RUTA_RESULTADOS
        / "perfil_gamma_total.csv",
        index=False,
    )

    perfil_bandas.to_csv(
        RUTA_RESULTADOS
        / "perfil_gamma_bandas.csv",
        index=False,
    )

    perfil_vencimientos.to_csv(
        RUTA_RESULTADOS
        / "perfil_gamma_vencimientos.csv",
        index=False,
    )

    flips_total.to_csv(
        RUTA_RESULTADOS
        / "gamma_flip_total.csv",
        index=False,
    )

    flips_bandas.to_csv(
        RUTA_RESULTADOS
        / "gamma_flip_bandas.csv",
        index=False,
    )

    flips_vencimientos.to_csv(
        RUTA_RESULTADOS
        / "gamma_flip_vencimientos.csv",
        index=False,
    )

    print()
    print("=" * 80)
    print("GAMMA FLIPS V3")
    print("=" * 80)

    print()
    print("TOTAL:")

    if flips_total.empty:
        print(
            "No existe cruce dentro del rango."
        )
    else:
        print(
            flips_total.to_string(
                index=False
            )
        )

    print()
    print("POR BANDA DTE:")

    if flips_bandas.empty:
        print(
            "No existen cruces."
        )
    else:
        print(
            flips_bandas.to_string(
                index=False
            )
        )

    print()
    print("POR VENCIMIENTO:")

    if flips_vencimientos.empty:
        print(
            "No existen cruces."
        )
    else:
        print(
            flips_vencimientos.to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()