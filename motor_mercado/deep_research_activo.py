"""Investigación por activo con estados explícitos y resultados trazables."""
from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from core.activos import resolver_activo
from core.datos import obtener_proveedor
from core.serializacion import serializar_json
from motor_mercado.analisis_universal import analizar_activo_universal
from motor_mercado.forecast_universal import ejecutar_forecast
from motor_mercado.regimen_universal import analizar_regimen_universal
from motor_opciones.cadena_opciones import enriquecer_cadena
from motor_opciones.calidad_cadena import evaluar_calidad_cadena
from motor_opciones.dealer_universal import calcular_exposiciones_dealer, resumir_dealer
from motor_opciones.dealer_por_vencimiento import analizar_dealer_por_vencimiento
from motor_opciones.escenarios_opciones import generar_graficas_escenarios
from motor_opciones.graficas_avanzadas import generar_pack_graficas
from motor_opciones.griegas_universales import aplicar_griegas
from motor_opciones.indice_graficas import generar_indice_graficas
from motor_opciones.movimiento_esperado import calcular_movimiento_esperado

RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_RESULTADOS = RUTA_BASE / "resultados" / "deep_research"
LOGGER = logging.getLogger(__name__)


def limpiar_simbolo(simbolo: str) -> str:
    """Normaliza una etiqueta sin permitir rutas fuera de resultados."""
    nombre = re.sub(r"[^A-Za-z0-9_.-]", "_", simbolo).strip("._")
    if not nombre:
        raise ValueError("Símbolo no válido para resultados.")
    return nombre


def obtener_cadena_multi_vencimiento(
    simbolo: str,
    numero_vencimientos: int = 12,
    ruta_auditoria: Path | None = None,
) -> tuple[pd.DataFrame, float]:
    """Obtiene y audita cada vencimiento; no oculta coberturas incompletas."""
    if numero_vencimientos < 1:
        raise ValueError("Se necesita al menos un vencimiento.")
    activo = resolver_activo(simbolo)
    proveedor = obtener_proveedor(activo.proveedor)
    spot = proveedor.obtener_precio_actual(activo)
    vencimientos = sorted(proveedor.listar_vencimientos_opciones(activo))[:numero_vencimientos]
    if not vencimientos:
        raise RuntimeError(f"No existen vencimientos para {simbolo}.")
    cadenas, rechazados, calidad = [], [], []
    errores = {}
    for vencimiento in vencimientos:
        try:
            cadena = proveedor.obtener_cadena_opciones(activo=activo, vencimiento=vencimiento)
            if cadena.empty:
                raise ValueError("Cadena vacía del proveedor.")
            cadena = enriquecer_cadena(cadena=cadena, spot=spot)
            valida, descartada, informe = evaluar_calidad_cadena(cadena)
            calidad.append({"vencimiento": vencimiento, **informe})
            rechazados.append(descartada)
            if valida.empty:
                raise ValueError("Ningún contrato supera los controles de calidad.")
            valida = aplicar_griegas(valida, spot)
            valida = calcular_exposiciones_dealer(valida, spot)
            valida.attrs = {}
            cadenas.append(valida)
        except Exception as error:
            errores[vencimiento] = str(error)
            LOGGER.warning("Opciones %s %s: %s", simbolo, vencimiento, error)
    if ruta_auditoria is not None:
        if rechazados:
            pd.concat(rechazados, ignore_index=True).to_csv(
                ruta_auditoria / "contratos_rechazados.csv", index=False
            )
        (ruta_auditoria / "calidad_opciones.json").write_text(
            json.dumps(serializar_json({"vencimientos": calidad, "errores": errores}),
                       ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
        )
    if not cadenas:
        raise RuntimeError(f"No se obtuvo ninguna cadena válida: {errores}")
    resultado = pd.concat(cadenas, ignore_index=True)
    resultado.attrs["errores_vencimientos"] = errores
    resultado.attrs["calidad"] = calidad
    return resultado, spot


def _revision_codigo() -> dict[str, object]:
    """Registra revisión y cambios locales sin modificar el índice Git."""
    try:
        comando = ["git", "-c", f"safe.directory={RUTA_BASE.as_posix()}", "--no-optional-locks"]
        revision = subprocess.check_output(
            comando + ["rev-parse", "HEAD"], cwd=RUTA_BASE, text=True, stderr=subprocess.DEVNULL
        ).strip()
        estado = subprocess.check_output(
            comando + ["status", "--porcelain"], cwd=RUTA_BASE, text=True, stderr=subprocess.DEVNULL
        )
        return {"commit": revision, "cambios_locales": bool(estado.strip())}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "cambios_locales": None}


def ejecutar_deep_research_activo(
    ticker: str,
    horizonte: int | None = None,
    numero_vencimientos: int = 12,
    dte_escenarios: int = 35,
    modelos: list[str] | None = None,
) -> dict[str, Any]:
    """Ejecuta módulos independientes; sin horizonte usa 5/20/60 sesiones.

    Devuelve OK, PARCIAL o ERROR. Los descartes y fallos de cada etapa quedan
    registrados; nunca se sobrescriben las ejecuciones anteriores.
    """
    if horizonte is not None and (
        isinstance(horizonte, bool) or not isinstance(horizonte, int) or not 1 <= horizonte <= 512
    ):
        raise ValueError("Horizonte fuera de 1..512 sesiones.")
    if numero_vencimientos < 1 or dte_escenarios < 1:
        raise ValueError("Vencimientos y DTE objetivo deben ser positivos.")
    activo = resolver_activo(ticker)
    ticker = activo.simbolo
    inicio = datetime.now(timezone.utc)
    ruta = RUTA_RESULTADOS / limpiar_simbolo(ticker) / inicio.strftime("%Y%m%d_%H%M%S_%f")
    ruta.mkdir(parents=True, exist_ok=False)
    ruta_graficas = ruta / "graficas"
    estados: dict[str, dict[str, object]] = {}

    def etapa(nombre, funcion):
        try:
            valor = funcion()
            estados[nombre] = {"estado": "OK"}
            return valor
        except Exception as error:
            estados[nombre] = {"estado": "ERROR", "error": str(error)}
            LOGGER.exception("Deep Research %s: %s", ticker, nombre)
            return None

    mercado = etapa("mercado", lambda: analizar_activo_universal(activo)) or {}
    regimen = etapa("regimen", lambda: analizar_regimen_universal(ticker)) or {}
    if mercado.get("advertencias"):
        estados["mercado"] = {"estado": "PARCIAL", "advertencias": mercado["advertencias"]}
    forecasts = {}
    horizontes = [horizonte] if horizonte is not None else [5, 20, 60]
    for h in horizontes:
        def calcular_forecast():
            tabla = ejecutar_forecast(simbolo=ticker, horizonte=h, modelos=modelos)
            tabla.to_csv(ruta / f"forecast_{h}d.csv", index=False)
            return tabla
        tabla = etapa(f"forecast_{h}d", calcular_forecast)
        if tabla is not None:
            forecasts[str(h)] = tabla.to_dict(orient="records")
            if tabla.attrs.get("errores_modelos"):
                estados[f"forecast_{h}d"] = {"estado": "PARCIAL", "errores_modelos": tabla.attrs["errores_modelos"]}

    dealer, por_vencimiento, graficas = {}, [], {}
    movimientos = []
    spot = mercado.get("precio")
    if activo.capacidades.opciones:
        resultado_opciones = etapa("opciones", lambda: obtener_cadena_multi_vencimiento(
            ticker, numero_vencimientos, ruta_auditoria=ruta
        ))
        if resultado_opciones is not None:
            cadena, spot = resultado_opciones
            cadena.to_csv(ruta / "cadena_opciones.csv", index=False)
            rechazos = sum(x["contratos_rechazados"] for x in cadena.attrs.get("calidad", []))
            if cadena.attrs.get("errores_vencimientos") or rechazos:
                estados["opciones"] = {
                    "estado": "PARCIAL", "contratos_rechazados": rechazos,
                    "errores_vencimientos": cadena.attrs.get("errores_vencimientos", {}),
                }
            def calcular_movimientos():
                archivo_rechazos = ruta / "contratos_rechazados.csv"
                descartados = pd.read_csv(archivo_rechazos) if archivo_rechazos.exists() else None
                tabla = calcular_movimiento_esperado(cadena, spot, rechazados=descartados)
                tabla.to_csv(ruta / "expected_move_por_vencimiento.csv", index=False)
                return tabla
            tabla_movimientos = etapa("expected_move", calcular_movimientos)
            if tabla_movimientos is not None:
                movimientos = tabla_movimientos.to_dict(orient="records")
                incompletos = int((tabla_movimientos["estado"] != "OK").sum())
                if incompletos:
                    estados["expected_move"] = {
                        "estado": "PARCIAL", "vencimientos_sin_estimacion": incompletos,
                    }
            def calcular_dealer():
                total = resumir_dealer(cadena)
                tabla, perfil = analizar_dealer_por_vencimiento(cadena, spot)
                pd.DataFrame([total]).to_csv(ruta / "dealer.csv", index=False)
                tabla_csv = tabla.copy()
                tabla_csv["gamma_flips"] = tabla_csv["gamma_flips"].map(json.dumps)
                tabla_csv.to_csv(ruta / "dealer_por_vencimiento.csv", index=False)
                perfil.to_csv(ruta / "perfil_gamma_por_vencimiento.csv", index=False)
                return total, tabla.to_dict(orient="records")
            resultado_dealer = etapa("dealer", calcular_dealer)
            if resultado_dealer is not None:
                dealer, por_vencimiento = resultado_dealer
            graficas.update(etapa("graficas", lambda: generar_pack_graficas(
                ticker=ticker, cadena=cadena, spot=spot, ruta_base=ruta_graficas
            )) or {})
            graficas.update(etapa("escenarios", lambda: generar_graficas_escenarios(
                ticker=ticker, cadena=cadena, spot=spot, ruta_base=ruta_graficas,
                dte_objetivo=dte_escenarios,
            )) or {})
        else:
            for nombre in ("dealer", "expected_move", "graficas", "escenarios"):
                estados[nombre] = {"estado": "BLOQUEADO", "error": "Opciones no disponibles"}
    else:
        estados["opciones"] = {"estado": "NO_COMPATIBLE"}
        estados["expected_move"] = {"estado": "NO_COMPATIBLE"}
    if graficas:
        indice = etapa("indice_graficas", lambda: generar_indice_graficas(
            ticker=ticker, graficas=graficas, ruta_salida=ruta_graficas / "indice_graficas.html"
        ))
        if indice is not None:
            graficas["indice_graficas"] = str(indice)

    correctos = sum(x["estado"] == "OK" for x in estados.values())
    problemas = any(x["estado"] in {"ERROR", "PARCIAL", "BLOQUEADO"} for x in estados.values())
    estado = "PARCIAL" if problemas and correctos else "ERROR" if problemas else "OK"
    resumen = {
        "ticker": ticker, "clase": activo.clase.value, "estado": estado, "spot": spot,
        "regimen": regimen.get("regimen_global"), "score_regimen": regimen.get("score_regimen"),
        **{k: mercado.get(k) for k in ("retorno_20d", "retorno_60d", "vol20", "vol60", "drawdown_actual")},
        "beta": mercado.get("beta60"), "correlacion_benchmark": mercado.get("correlacion60"),
        "graficas_generadas": len(graficas), "ruta": str(ruta),
        **{f"dealer_{k}": v for k, v in dealer.items()},
    }
    pd.DataFrame([mercado]).to_csv(ruta / "mercado.csv", index=False)
    pd.DataFrame([{k: v for k, v in regimen.items() if k != "componentes_regimen"}]).to_csv(ruta / "regimen.csv", index=False)
    pd.DataFrame([resumen]).to_csv(ruta / "resumen.csv", index=False)
    pd.DataFrame([{"grafica": k, "ruta": v} for k, v in graficas.items()], columns=["grafica", "ruta"]).to_csv(ruta / "indice_graficas.csv", index=False)
    resultado = {
        "version_esquema": 2, "ticker": ticker, "estado": estado, "estados": estados,
        "ruta_resultados": str(ruta), "resumen": resumen, "mercado": mercado,
        "regimen": regimen, "forecast": forecasts, "dealer": dealer,
        "dealer_por_vencimiento": por_vencimiento, "graficas": graficas,
        "expected_move_por_vencimiento": movimientos,
        "procedencia": {
            "inicio_utc": inicio.isoformat(), "fin_utc": datetime.now(timezone.utc).isoformat(),
            "fecha_mercado": mercado.get("fecha"), "proveedor": activo.proveedor,
            "python": platform.python_version(), **_revision_codigo(),
            "parametros": {"horizontes": horizontes, "modelos": modelos,
                           "numero_vencimientos": numero_vencimientos, "dte_escenarios": dte_escenarios},
            "convenciones": {"dealer": "PROXY_CALL_SHORT_PUT_LONG", "walls": "MAX_OI_POR_STRIKE",
                             "pricing": "BLACK_SCHOLES_EUROPEO", "tipo_interes": 0.04,
                             "dividendo": 0.01, "multiplicador": 100},
            "expected_move": {"base_dias": 365, "distancia_atm_maxima": 0.02,
                              "iv_atm": "MEDIA_CALL_PUT", "centro_limites": "SPOT",
                              "probabilidad_calibrada": False},
        },
    }
    (ruta / "informe.json").write_text(json.dumps(
        serializar_json(resultado), ensure_ascii=False, indent=2, allow_nan=False
    ), encoding="utf-8")
    print(f"DEEP RESEARCH {ticker}: {estado} — {ruta}")
    return resultado
