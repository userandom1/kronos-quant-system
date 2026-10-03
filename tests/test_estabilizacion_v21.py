"""Regresiones deterministas de V2.1; no descargan datos ni pesos."""
from __future__ import annotations

import asyncio
import json
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from core.activos import resolver_activo
from core.modelos.modelo_base import ResultadoForecast
from motor_mercado.forecast_universal import ejecutar_forecast
from motor_mercado.metricas_mercado import volatilidad_anualizada
from motor_opciones.calidad_cadena import evaluar_calidad_cadena
from motor_opciones.dealer_por_vencimiento import (
    analizar_dealer_por_vencimiento, buscar_cruces_gamma,
)
from motor_opciones.dealer_universal import (
    calcular_exposiciones_dealer, calcular_niveles_dealer, resumir_dealer,
)
from motor_opciones.griegas import ParametrosOpcion, gamma, vanna_por_punto
from motor_opciones.griegas_universales import aplicar_griegas
from motor_opciones.options_flow_universal import comparar_snapshots
from motor_portfolio.optimizador_universal import pesos_min_varianza, pesos_signal_tilted
from motor_riesgo.risk_engine_universal import max_drawdown
from motor_riesgo.metricas_riesgo import max_drawdown as drawdown_anterior


def cadena_sintetica() -> pd.DataFrame:
    """Dos vencimientos con calls/puts, cotizaciones utilizables y OI conocido."""
    return pd.DataFrame({
        "vencimiento": ["2027-01-15"] * 2 + ["2027-02-19"] * 2,
        "dte": [30., 30., 60., 60.],
        "strike": [100., 100., 100., 100.],
        "tipo_opcion": ["CALL", "PUT", "CALL", "PUT"],
        "bid": [1.9] * 4, "ask": [2.1] * 4, "mid": [2.] * 4,
        "iv": [.25] * 4, "open_interest": [100., 200., 300., 100.],
        "volumen": [100.] * 4, "ultimo": [2.1] * 4,
        "contract_symbol": ["C1", "P1", "C2", "P2"],
        "spot": [100.] * 4,
    })


def cadena_calculada() -> pd.DataFrame:
    return calcular_exposiciones_dealer(aplicar_griegas(cadena_sintetica(), 100.), 100.)


class RiesgoPortfolio(unittest.TestCase):
    def test_drawdown_incluye_capital_inicial(self):
        for funcion in [max_drawdown, drawdown_anterior]:
            self.assertAlmostEqual(funcion(pd.Series([-.1, -.1])), -.19)
            self.assertAlmostEqual(funcion(pd.Series([-.2, .1])), -.2)
            self.assertEqual(funcion(pd.Series([.1, .2])), 0.)
            self.assertEqual(funcion(pd.Series([-1., 0.])), -1.)

    def test_drawdown_rechaza_retornos_imposibles(self):
        with self.assertRaises(ValueError):
            max_drawdown(pd.Series([-1.1]))

    def test_portfolio_uno_y_dos_activos(self):
        datos = pd.DataFrame({"A": [.01, -.02, .03], "B": [-.01, .02, .01]})
        for n in [1, 2]:
            retornos = datos.iloc[:, :n]
            for pesos in [pesos_min_varianza(retornos), pesos_signal_tilted(retornos, pd.Series(0., index=retornos.columns))]:
                self.assertAlmostEqual(pesos.sum(), 1.)
                self.assertTrue((pesos >= 0).all())

    def test_limite_explicito_inviable(self):
        with self.assertRaisesRegex(ValueError, "inviable"):
            pesos_min_varianza(pd.DataFrame({"A": [.01, .02], "B": [.02, .03]}), .35)

    def test_retornos_nan(self):
        with self.assertRaises(ValueError):
            pesos_min_varianza(pd.DataFrame({"A": [.01, np.nan]}))

    def test_anualizacion(self):
        datos = pd.Series([.01, -.02, .03])
        self.assertAlmostEqual(volatilidad_anualizada(datos, 3, 365) /
                               volatilidad_anualizada(datos, 3, 252), np.sqrt(365 / 252))

    def test_alias_indices(self):
        self.assertEqual(resolver_activo("SPX").simbolo, "^GSPC")
        self.assertEqual(resolver_activo("VIX").clase.value, "INDEX")
        self.assertEqual(resolver_activo("DIA").clase.value, "ETF")


class CalidadGreeks(unittest.TestCase):
    def test_cadena_valida(self):
        validos, rechazados, informe = evaluar_calidad_cadena(cadena_sintetica())
        self.assertEqual(len(validos), 4)
        self.assertTrue(rechazados.empty)
        self.assertEqual(informe["contratos_rechazados"], 0)

    def test_motivos_rechazo(self):
        datos = cadena_sintetica()
        datos.loc[0, "ask"] = 0
        datos.loc[1, "iv"] = .00001
        datos.loc[2, "dte"] = 0
        datos.loc[3, "bid"] = 3
        validos, rechazados, informe = evaluar_calidad_cadena(datos)
        self.assertTrue(validos.empty)
        self.assertEqual(len(rechazados), 4)
        self.assertEqual(informe["motivos"]["dte_no_positivo"], 1)
        self.assertTrue(rechazados["motivos_calidad"].str.len().gt(0).all())

    def test_duplicados(self):
        datos = cadena_sintetica()
        validos, rechazados, _ = evaluar_calidad_cadena(pd.concat([datos, datos.iloc[:1]]))
        self.assertEqual(len(validos), 4)
        self.assertEqual(len(rechazados), 1)

    def test_tiempo_fraccionario_no_se_redondea_a_un_dia(self):
        datos = cadena_sintetica().iloc[:1].copy()
        datos["dte"] = .25
        calculado = aplicar_griegas(datos, 100.)
        parametro = ParametrosOpcion(100., 100., .25 / 365, .25, .04, .01, "call")
        self.assertAlmostEqual(calculado["gamma"].iloc[0], gamma(parametro), places=10)

    def test_0dte_no_se_inventa(self):
        datos = cadena_sintetica()
        datos["dte"] = 0
        self.assertTrue(aplicar_griegas(datos, 100.).empty)

    def test_vanna_analitica(self):
        datos = cadena_sintetica().iloc[:1]
        calculado = aplicar_griegas(datos, 100.)
        parametro = ParametrosOpcion(100., 100., 30. / 365, .25, .04, .01, "call")
        self.assertAlmostEqual(calculado["vanna_1pt"].iloc[0], vanna_por_punto(parametro), places=10)


class DealerVencimientos(unittest.TestCase):
    def test_totales_reconcilian(self):
        datos = cadena_calculada()
        tabla, perfil = analizar_dealer_por_vencimiento(datos, 100.)
        self.assertEqual(len(tabla), 2)
        self.assertEqual(tabla["contratos"].sum(), len(datos))
        total = resumir_dealer(datos)
        for columna in ["net_gex_1pct", "net_dex", "net_vanna_1pt", "net_charm_dia"]:
            self.assertAlmostEqual(tabla[columna].sum(), total[columna])
        en_spot = perfil[np.isclose(perfil["spot"], 100.)]
        self.assertAlmostEqual(en_spot["net_gex_1pct"].sum(), total["net_gex_1pct"])

    def test_walls_agregan_oi_por_strike(self):
        datos = cadena_calculada()
        datos.loc[2, "strike"] = 105.
        datos.loc[0, "open_interest"] = 200.
        extra = datos.iloc[:1].copy()
        extra["open_interest"] = 200.
        datos = pd.concat([datos, extra], ignore_index=True)
        self.assertEqual(calcular_niveles_dealer(datos)["call_wall"], 100.)

    def test_lado_ausente_y_nodos_con_signo(self):
        datos = cadena_calculada().query("tipo_opcion == 'CALL'")
        niveles = calcular_niveles_dealer(datos)
        self.assertIsNone(niveles["put_wall"])
        self.assertIsNone(niveles["gamma_node_positivo"])

    def test_cero_oi_no_produce_wall(self):
        datos = cadena_calculada()
        datos["open_interest"] = 0
        self.assertIsNone(calcular_niveles_dealer(datos)["call_wall"])

    def test_cruces_multiples_y_cero_exacto(self):
        self.assertEqual(buscar_cruces_gamma(np.array([1., 2., 3.]), np.array([-1., 0., 1.])), [2.])
        self.assertEqual(buscar_cruces_gamma(np.array([1., 2., 3.]), np.array([-1., 1., -1.])), [1.5, 2.5])
        self.assertEqual(buscar_cruces_gamma(np.array([1., 2., 3.]), np.zeros(3)), [])
        self.assertEqual(buscar_cruces_gamma(np.array([1., 2., 3.]), np.array([1., 0., 1.])), [])

    def test_agregacion_antigua_no_usa_dte_como_clave(self):
        from motor_opciones.exposiciones import agregar_por_vencimiento
        columnas = ["dex_dealer", "gex_1pct_dealer", "theta_exposure_dia_dealer",
                    "vega_exposure_1pt_dealer", "vanna_exposure_1pt_dealer", "charm_exposure_dia_dealer"]
        datos = pd.DataFrame({"vencimiento": ["2027-01-15"] * 2, "dte": [30., 30.00001],
                              **{c: [1., 2.] for c in columnas}})
        tabla = agregar_por_vencimiento(datos)
        self.assertEqual(len(tabla), 1)
        self.assertEqual(tabla["gex_1pct_dealer"].iloc[0], 3.)


class FlowForecast(unittest.TestCase):
    def test_flow_rechaza_captura_invertida_en_la_misma_sesion(self):
        anterior = cadena_sintetica()
        actual = anterior.copy()
        anterior["capturado_en"] = "2026-09-30T18:00:00Z"
        actual["capturado_en"] = "2026-09-30T17:00:00Z"
        with self.assertRaises(ValueError):
            comparar_snapshots(anterior, actual)

    def test_flow_rechaza_volumen_desconocido(self):
        datos = cadena_sintetica()
        datos.loc[0, "volumen"] = np.nan
        with self.assertRaises(ValueError):
            comparar_snapshots(datos, datos)

    def test_flow_retroceso_intradia_queda_marcado(self):
        anterior = cadena_sintetica()
        actual = anterior.copy()
        actual["volumen"] = 0
        flujo = comparar_snapshots(anterior, actual)
        self.assertTrue(flujo["volumen_retrocede"].all())
        self.assertEqual(flujo["delta_volumen"].sum(), 0.)

    def test_flow_cambio_sesion(self):
        anterior = cadena_sintetica()
        actual = anterior.copy()
        anterior["capturado_en"] = "2026-09-29T18:00:00Z"
        actual["capturado_en"] = "2026-09-30T18:00:00Z"
        actual["volumen"] = 20.
        flujo = comparar_snapshots(anterior, actual)
        self.assertEqual(flujo["delta_volumen"].sum(), 80.)
        self.assertTrue(flujo["cambio_sesion"].all())

    def test_flow_contrato_nuevo_sin_base(self):
        anterior = cadena_sintetica().iloc[:2]
        actual = cadena_sintetica()
        flujo = comparar_snapshots(anterior, actual)
        self.assertTrue(flujo.loc[flujo.sin_base_anterior, "delta_volumen"].eq(0).all())

    def test_flow_cotizacion_cero_no_es_buy(self):
        datos = cadena_sintetica()
        actual = datos.copy()
        actual["bid"] = actual["ask"] = actual["ultimo"] = 0
        actual["volumen"] = 200
        flujo = comparar_snapshots(datos, actual)
        self.assertTrue(flujo["ejecucion_proxy"].eq("DESCONOCIDA").all())
        self.assertEqual(flujo["premium_nuevo"].sum(), 0.)

    def test_forecast_conserva_modelos_sanos(self):
        bueno = Mock()
        bueno.predecir.return_value = ResultadoForecast(
            simbolo="QQQ", modelo="DRIFT", horizonte=5,
            precio_actual=100., precio_estimado=101., retorno_estimado=.01,
        )
        malo = Mock()
        malo.predecir.side_effect = RuntimeError("Modelo no disponible")
        with patch("motor_mercado.forecast_universal.obtener_proveedor"), patch(
            "motor_mercado.forecast_universal.obtener_modelo", side_effect=[bueno, malo]
        ):
            tabla = ejecutar_forecast("QQQ", 5, ["DRIFT", "KRONOS"])
        self.assertEqual(len(tabla), 1)
        self.assertIn("KRONOS", tabla.attrs["errores_modelos"])

    def test_horizonte_invalido(self):
        with self.assertRaises(ValueError):
            ejecutar_forecast("QQQ", 0)


class DeepResearch(unittest.TestCase):
    def setUp(self):
        from motor_mercado import deep_research_activo as modulo
        self.modulo = modulo
        base = Path(__file__).resolve().parents[1] / ".cache" / "pruebas"
        base.mkdir(parents=True, exist_ok=True)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temporal = self.stack.enter_context(tempfile.TemporaryDirectory(dir=base))
        self.ruta = Path(temporal)
        self.stack.enter_context(patch.object(modulo, "RUTA_RESULTADOS", self.ruta))
        self.stack.enter_context(patch.object(modulo, "_revision_codigo", return_value={"commit": "prueba"}))
        self.stack.enter_context(patch.object(modulo.LOGGER, "exception"))
        self.stack.enter_context(patch.object(modulo, "analizar_activo_universal", return_value={"precio": 100., "beta60": 1.2}))
        self.stack.enter_context(patch.object(modulo, "analizar_regimen_universal", return_value={"regimen_global": "NEUTRAL"}))
        self.forecast = self.stack.enter_context(patch.object(modulo, "ejecutar_forecast", return_value=pd.DataFrame({"modelo": ["DRIFT"]})))
        self.opciones = self.stack.enter_context(patch.object(modulo, "obtener_cadena_multi_vencimiento", return_value=(cadena_calculada(), 100.)))
        self.graficas = self.stack.enter_context(patch.object(modulo, "generar_pack_graficas", return_value={}))
        self.stack.enter_context(patch.object(modulo, "generar_graficas_escenarios", return_value={}))

    def test_horizonte_beta_informe_y_dealer_integrado(self):
        resultado = self.modulo.ejecutar_deep_research_activo("QQQ", horizonte=7)
        self.assertEqual(resultado["estado"], "OK")
        self.assertEqual(resultado["resumen"]["beta"], 1.2)
        self.assertEqual(list(resultado["forecast"]), ["7"])
        self.assertEqual(len(resultado["dealer_por_vencimiento"]), 2)
        informe = json.loads((Path(resultado["ruta_resultados"]) / "informe.json").read_text(encoding="utf-8"))
        self.assertEqual(informe["procedencia"]["parametros"]["horizontes"], [7])
        self.assertTrue((Path(resultado["ruta_resultados"]) / "dealer_por_vencimiento.csv").exists())
        self.assertTrue((Path(resultado["ruta_resultados"]) / "expected_move_por_vencimiento.csv").exists())
        self.assertEqual(len(informe["expected_move_por_vencimiento"]), 2)
        self.assertEqual(informe["expected_move_por_vencimiento"][0]["move_straddle_dolares"], 4.)

    def test_fallo_expected_move_no_oculta_dealer(self):
        with patch.object(self.modulo, "calcular_movimiento_esperado", side_effect=ValueError("Pareja inválida")):
            resultado = self.modulo.ejecutar_deep_research_activo("QQQ", horizonte=5)
        self.assertEqual(resultado["estado"], "PARCIAL")
        self.assertEqual(resultado["estados"]["expected_move"]["estado"], "ERROR")
        self.assertEqual(resultado["estados"]["dealer"]["estado"], "OK")

    def test_fallo_grafico_no_oculta_dealer(self):
        self.graficas.side_effect = RuntimeError("Error de gráfico")
        resultado = self.modulo.ejecutar_deep_research_activo("QQQ", horizonte=5)
        self.assertEqual(resultado["estado"], "PARCIAL")
        self.assertEqual(resultado["estados"]["graficas"]["estado"], "ERROR")
        self.assertEqual(resultado["estados"]["dealer"]["estado"], "OK")

    def test_fallo_opciones_explica_dependientes(self):
        self.opciones.side_effect = RuntimeError("Sin datos")
        resultado = self.modulo.ejecutar_deep_research_activo("QQQ", horizonte=5)
        self.assertEqual(resultado["estado"], "PARCIAL")
        self.assertEqual(resultado["estados"]["dealer"]["estado"], "BLOQUEADO")
        self.assertEqual(resultado["estados"]["expected_move"]["estado"], "BLOQUEADO")

    def test_horizontes_por_defecto(self):
        resultado = self.modulo.ejecutar_deep_research_activo("BTC-USD")
        self.assertEqual(list(resultado["forecast"]), ["5", "20", "60"])
        self.assertEqual(resultado["estados"]["opciones"]["estado"], "NO_COMPATIBLE")
        self.assertEqual(resultado["estados"]["expected_move"]["estado"], "NO_COMPATIBLE")


class API(unittest.TestCase):
    def test_rutas_pesadas_sin_bloquear_health(self):
        import httpx
        from dashboard_v2.servidor import app

        async def comprobar():
            transporte = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transporte, base_url="http://prueba") as cliente:
                tarea = asyncio.create_task(cliente.get("/api/v2/activo/QQQ"))
                await asyncio.sleep(.03)
                inicio = time.monotonic()
                health = await cliente.get("/api/v2/health")
                duracion = time.monotonic() - inicio
                self.assertEqual(health.status_code, 200)
                self.assertLess(duracion, .25)
                self.assertEqual((await tarea).status_code, 200)

        def lento(*args, **kwargs):
            time.sleep(.4)
            return {"estado": "OK"}

        with patch("dashboard_v2.servidor.api_activo", side_effect=lento), patch(
            "dashboard_v2.servidor.api_health", return_value={"operativo": True}
        ):
            asyncio.run(comprobar())

    def test_horizonte_invalido_http_400(self):
        from starlette.testclient import TestClient
        from dashboard_v2.servidor import app
        with TestClient(app) as cliente:
            self.assertEqual(cliente.get("/api/v2/activo/QQQ?horizonte=0").status_code, 400)


if __name__ == "__main__":
    unittest.main()
