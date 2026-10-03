"""Validación de fórmulas, parejas ATM y compatibilidad de informes."""
import json
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from motor_opciones.movimiento_esperado import (
    PoliticaMovimientoEsperado, calcular_movimiento_esperado,
)


def pareja(dte: float = 365) -> pd.DataFrame:
    return pd.DataFrame({
        "vencimiento": ["2027-10-01"] * 2, "dte": [dte] * 2,
        "strike": [100.] * 2, "tipo_opcion": ["CALL", "PUT"],
        "bid": [1.9, 2.9], "ask": [2.1, 3.1], "iv": [.2, .4],
        "open_interest": [200., 100.], "mid": [999., 999.],
    })


def test_formulas_unidades_y_limites():
    fila = calcular_movimiento_esperado(pareja(), 100.).iloc[0]
    assert fila.estado == "OK"
    assert fila.move_straddle_dolares == pytest.approx(5.)
    assert fila.move_straddle_pct == pytest.approx(.05)
    assert fila.iv_atm == pytest.approx(.3)
    assert fila.move_iv_dolares == pytest.approx(30.)
    assert fila.limite_inferior_straddle == pytest.approx(95.)
    assert fila.limite_superior_straddle == pytest.approx(105.)
    assert fila.limite_inferior_iv == pytest.approx(70.)
    assert fila.limite_superior_iv == pytest.approx(130.)
    assert fila.call_mid == pytest.approx(2.)  # Ignora el mid inconsistente recibido.


def test_iv_escala_con_raiz_del_tiempo_y_admite_fracciones():
    largo = calcular_movimiento_esperado(pareja(100.), 100.).iloc[0]
    corto = calcular_movimiento_esperado(pareja(25.), 100.).iloc[0]
    assert largo.move_iv_dolares == pytest.approx(2 * corto.move_iv_dolares)
    fraccion = calcular_movimiento_esperado(pareja(.5), 100.).iloc[0]
    assert fraccion.dte == .5
    assert fraccion.move_iv_dolares == pytest.approx(30 * np.sqrt(.5 / 365))


def test_pareja_comparte_strike_sin_sustituir_atm_incompleto():
    datos = pareja().iloc[:1].copy()
    lejos = pareja()
    lejos["strike"] = 101.
    fila = calcular_movimiento_esperado(pd.concat([datos, lejos]), 100.).iloc[0]
    assert fila.estado == "SIN_PAREJA_ATM"
    assert pd.isna(fila.move_iv_dolares)


def test_rechazos_preservan_el_strike_original():
    invalida = pareja()
    invalida["ask"] = 20.
    valida = pareja()
    valida["strike"] = 101.
    fila = calcular_movimiento_esperado(valida, 100., rechazados=invalida).iloc[0]
    assert fila.strike_atm == 100.
    assert fila.estado == "SIN_PAREJA_ATM"
    assert fila.contratos_rechazados == 2


def test_no_mezcla_fechas_ni_tipos():
    datos = pareja()
    datos.loc[1, "vencimiento"] = "2027-11-01"
    tabla = calcular_movimiento_esperado(datos, 100.)
    assert len(tabla) == 2
    assert tabla.estado.eq("SIN_PAREJA_ATM").all()


def test_dte_inconsistente_no_produce_estimaciones():
    datos = pareja()
    datos.loc[1, "dte"] = 364.
    fila = calcular_movimiento_esperado(datos, 100.).iloc[0]
    assert fila.estado == "DTE_INCONSISTENTE"
    assert pd.isna(fila.move_straddle_dolares)


def test_distancia_atm_y_politica_configurable():
    datos = pareja()
    datos["strike"] = 110.
    assert calcular_movimiento_esperado(datos, 100.).iloc[0].estado == "ATM_LEJANO"
    assert calcular_movimiento_esperado(datos, 100., PoliticaMovimientoEsperado(.15)).iloc[0].estado == "OK"


def test_empate_de_strikes_es_determinista():
    bajo, alto = pareja(), pareja()
    bajo["strike"], alto["strike"] = 99., 101.
    fila = calcular_movimiento_esperado(pd.concat([alto, bajo]), 100.).iloc[0]
    assert fila.strike_atm == 99.


@pytest.mark.parametrize("cambio", [{"dte": 0.}, {"iv": 0.}, {"ask": 0.}, {"bid": 10.}, {"iv": np.nan}])
def test_calidad_invalida_no_inventa_movimiento(cambio):
    datos = pareja().assign(**cambio)
    fila = calcular_movimiento_esperado(datos, 100.).iloc[0]
    assert fila.estado == "SIN_CONTRATOS_VALIDOS"
    assert pd.isna(fila.move_iv_dolares)


@pytest.mark.parametrize("spot", [0., -1., np.nan, np.inf])
def test_spot_invalido(spot):
    with pytest.raises(ValueError):
        calcular_movimiento_esperado(pareja(), spot)


def test_duplicados_y_fechas_equivalentes():
    datos = pareja()
    copia = datos.copy()
    copia["vencimiento"] = "2027-10-01 00:00:00"
    tabla = calcular_movimiento_esperado(pd.concat([datos, copia]), 100.)
    assert len(tabla) == 1
    assert tabla.iloc[0].contratos_rechazados == 2


def test_api_recalcula_historico_sin_escribirlo(tmp_path):
    from motor_sistema.api_v2 import api_informe
    informe = tmp_path / "informe.json"
    contenido = json.dumps({"ticker": "QQQ", "resumen": {"spot": 100.}, "version_esquema": 2})
    informe.write_text(contenido, encoding="utf-8")
    pareja().to_csv(tmp_path / "cadena_opciones.csv", index=False)
    with patch("pathlib.Path.glob", return_value=[informe]):
        respuesta = api_informe("QQQ")
    assert respuesta["expected_move_por_vencimiento"][0]["move_straddle_dolares"] == pytest.approx(5.)
    assert respuesta["procedencia_expected_move"]["modo"] == "RECALCULADO_HISTORICO_EN_MEMORIA"
    assert informe.read_text(encoding="utf-8") == contenido


def test_api_respeta_estimaciones_ya_guardadas(tmp_path):
    from motor_sistema.api_v2 import api_informe
    informe = tmp_path / "informe.json"
    informe.write_text(json.dumps({"expected_move_por_vencimiento": []}), encoding="utf-8")
    with patch("pathlib.Path.glob", return_value=[informe]), patch(
        "motor_sistema.api_v2.calcular_movimiento_esperado", side_effect=AssertionError("No recalcular")
    ):
        assert api_informe("QQQ")["expected_move_por_vencimiento"] == []
