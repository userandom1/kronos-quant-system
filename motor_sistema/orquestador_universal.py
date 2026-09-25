from __future__ import annotations

from datetime import datetime

from core.activos import resolver_activo
from motor_mercado.forecast_universal import (
    construir_ensemble_simple,
    ejecutar_forecast,
)
from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
)
from motor_opciones.dealer_universal import (
    calcular_exposiciones_dealer,
    resumir_dealer,
)
from motor_opciones.griegas_universales import (
    aplicar_griegas,
)
from motor_opciones.options_engine_universal import (
    ejecutar_options_engine,
)
from motor_sistema.resultado_activo import (
    ResultadoActivo,
    ResultadoMotor,
)


def ejecutar_market_regime(
    simbolo: str,
) -> ResultadoMotor:
    """Ejecuta Market Regime Universal."""

    try:
        resultado = analizar_regimen_universal(
            simbolo
        )

        componentes = resultado.pop(
            "componentes_regimen",
            None,
        )

        if componentes is not None:
            resultado[
                "componentes_regimen"
            ] = componentes

        return ResultadoMotor(
            nombre="market_regime",
            estado="OK",
            datos=resultado,
        )

    except Exception as error:
        return ResultadoMotor(
            nombre="market_regime",
            estado="ERROR",
            error=str(error),
        )


def ejecutar_forecast_engine(
    simbolo: str,
    horizonte: int,
) -> ResultadoMotor:
    """Ejecuta Forecast Engine Universal."""

    try:
        resultados = ejecutar_forecast(
            simbolo=simbolo,
            horizonte=horizonte,
        )

        ensemble = construir_ensemble_simple(
            resultados
        )

        modelos = resultados.to_dict(
            orient="records"
        )

        return ResultadoMotor(
            nombre="forecast",
            estado="OK",
            datos={
                "horizonte": horizonte,
                "ensemble": ensemble,
                "modelos": modelos,
            },
        )

    except Exception as error:
        return ResultadoMotor(
            nombre="forecast",
            estado="ERROR",
            error=str(error),
        )


def ejecutar_options_engine_sistema(
    simbolo: str,
) -> ResultadoMotor:
    """Ejecuta opciones, Greeks y dealer."""

    try:
        activo = resolver_activo(
            simbolo
        )

        resultado = ejecutar_options_engine(
            activo
        )

        cadena = aplicar_griegas(
            cadena=resultado.cadena,
            spot=resultado.spot,
        )

        cadena = calcular_exposiciones_dealer(
            cadena=cadena,
            spot=resultado.spot,
        )

        dealer = resumir_dealer(
            cadena
        )

        return ResultadoMotor(
            nombre="opciones",
            estado="OK",
            datos={
                "spot": resultado.spot,
                "vencimiento": (
                    resultado.vencimiento
                ),
                "contratos": len(
                    cadena
                ),
                "resumen_cadena": (
                    resultado.resumen
                ),
                "dealer": dealer,
            },
        )

    except Exception as error:
        return ResultadoMotor(
            nombre="opciones",
            estado="ERROR",
            error=str(error),
        )


def analizar_activo_completo(
    simbolo: str,
    horizonte_forecast: int = 20,
) -> ResultadoActivo:
    """Ejecuta todos los motores compatibles."""

    activo = resolver_activo(
        simbolo
    )

    resultado = ResultadoActivo(
        simbolo=activo.simbolo,
        clase=activo.clase.value,
        timestamp=datetime.now(),
    )

    resultado.agregar(
        ejecutar_market_regime(
            activo.simbolo
        )
    )

    if activo.capacidades.forecast:
        resultado.agregar(
            ejecutar_forecast_engine(
                activo.simbolo,
                horizonte_forecast,
            )
        )

    else:
        resultado.agregar(
            ResultadoMotor(
                nombre="forecast",
                estado="NO_COMPATIBLE",
            )
        )

    if activo.capacidades.opciones:
        resultado.agregar(
            ejecutar_options_engine_sistema(
                activo.simbolo
            )
        )

    else:
        resultado.agregar(
            ResultadoMotor(
                nombre="opciones",
                estado="NO_COMPATIBLE",
            )
        )

    return resultado