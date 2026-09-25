from __future__ import annotations

from dataclasses import dataclass

from core.activos import resolver_activo
from core.activos.universos import listar_universos
from core.datos import (
    listar_proveedores,
    obtener_proveedor,
)
from core.datos.cache_datos import CACHE_DATOS
from core.modelos.registro_modelos import (
    listar_modelos,
)


@dataclass(slots=True)
class ResultadoCheck:
    """Resultado individual de un health check."""

    componente: str
    estado: str
    detalle: str


def comprobar_sistema(
    comprobar_datos: bool = True,
) -> tuple[
    bool,
    list[ResultadoCheck],
]:
    """Comprueba el núcleo de V2."""

    resultados: list[
        ResultadoCheck
    ] = []

    try:
        activo = resolver_activo(
            "QQQ"
        )

        resultados.append(
            ResultadoCheck(
                "Asset Resolver",
                "OK",
                activo.clase.value,
            )
        )

    except Exception as error:
        resultados.append(
            ResultadoCheck(
                "Asset Resolver",
                "ERROR",
                str(error),
            )
        )

    proveedores = listar_proveedores()

    resultados.append(
        ResultadoCheck(
            "Data Providers",
            (
                "OK"
                if proveedores
                else "ERROR"
            ),
            str(
                proveedores
            ),
        )
    )

    modelos = listar_modelos()

    resultados.append(
        ResultadoCheck(
            "Forecast Models",
            (
                "OK"
                if modelos
                else "ERROR"
            ),
            str(
                modelos
            ),
        )
    )

    universos = listar_universos()

    resultados.append(
        ResultadoCheck(
            "Universos",
            (
                "OK"
                if universos
                else "ERROR"
            ),
            str(
                universos
            ),
        )
    )

    if comprobar_datos:
        try:
            activo = resolver_activo(
                "QQQ"
            )

            proveedor = obtener_proveedor(
                activo.proveedor
            )

            datos = proveedor.obtener_historico(
                activo,
                periodo="5d",
                intervalo="1d",
            )

            resultados.append(
                ResultadoCheck(
                    "Market Data",
                    "OK",
                    f"{len(datos)} filas",
                )
            )

        except Exception as error:
            resultados.append(
                ResultadoCheck(
                    "Market Data",
                    "ERROR",
                    str(error),
                )
            )

    cache = CACHE_DATOS.estadisticas()

    resultados.append(
        ResultadoCheck(
            "Data Cache",
            "OK",
            str(
                cache
            ),
        )
    )

    correcto = all(
        resultado.estado == "OK"
        for resultado in resultados
    )

    return correcto, resultados


def main() -> None:
    """Ejecuta Health Check V2."""

    correcto, resultados = (
        comprobar_sistema()
    )

    print(
        "=" * 90
    )

    print(
        "HEALTH CHECK — QUANT PLATFORM V2"
    )

    print(
        "=" * 90
    )

    for resultado in resultados:
        print(
            f"{resultado.componente:<20} | "
            f"{resultado.estado:<5} | "
            f"{resultado.detalle}"
        )

    print()

    print(
        "SISTEMA: "
        + (
            "OPERATIVO"
            if correcto
            else "CON ERRORES"
        )
    )

    raise SystemExit(
        0 if correcto else 1
    )


if __name__ == "__main__":
    main()