# Quant Platform — estado contrastado

Actualizado el 2 de octubre de 2026. Código, Git y tests prevalecen. Documentos originales preservados íntegros en `documentacion/historico/`.

## Git y entorno

Rama activa: quant-platform-v2. V1: kronos-quant-v1. Existen master, origin/* y upstream/master; tags v1.0.0 y v2.0.0. La auditoría empezó con una fusión pendiente de V1 (4c2e457) en V2 (ddb6410) y README conflictivo. Se conservan los archivos/imágenes preparados antes de la auditoría. No se publica al remoto en esta tarea.

Windows, D:\02_Herramientas\kronos, Python 3.12.9, PyTorch 2.6.0+cu126, CUDA disponible, GTX 1080 Ti 11 GB. Dependencias directas recogidas y pip check sin conflictos; no se ha probado una instalación desde cero.

## Estructura y dependencias

| Capa | Módulos | Dependencias |
|---|---|---|
| Activos/datos | core/activos, core/datos | Reglas de símbolos, YFinance, normalización, retries, caché |
| Mercado | motor_mercado/analisis_universal.py, regimen_universal.py | Históricos y benchmark |
| Forecast | forecast_universal.py, core/modelos | Datos; Drift, Momentum, Kronos; ensemble simple |
| Opciones/calidad | cadena_opciones.py, options_engine_universal.py, calidad_cadena.py | Spot, vencimientos, cotizaciones, IV, DTE y OI |
| Greeks | griegas_universales.py y griegas.py legacy | Cadena, Black-Scholes, tasas/dividendos asumidos |
| Dealer | dealer_universal.py, dealer_por_vencimiento.py | Greeks, OI, spot y signo proxy |
| Flow | snapshot_opciones.py, options_flow_universal.py | Dos snapshots, timestamps UTC y sesión Nueva York |
| Escenarios | escenarios_opciones.py, graficas_avanzadas.py, indice_graficas.py | Cadena, contratos ITM/ATM/OTM y pricing |
| Portfolio | portfolio_universal.py, optimizador_universal.py | Históricos alineados y señales |
| Riesgo | risk_engine_universal.py, metricas_riesgo.py, stress_test.py | Retornos, pesos, benchmark y shocks |
| Sistema/UI | motor_sistema, dashboard_v2; dashboard V1 separado | Orquestadores, API e informes persistidos |
| Deep Research | deep_research_activo.py y CLI motor_sistema.deep_research | Mercado, régimen, forecast, opciones/dealer, escenarios y reporting |

model/, finetune/, examples/ y webui/ proceden del modelo original. pruebas/ contiene comprobaciones manuales, algunas con red; tests/ y motor_opciones/pruebas/probar_griegas.py forman la suite automatizada.

## Correcto en los documentos anteriores

La arquitectura modular, las interfaces de proveedores/modelos y los motores descritos existen. Los valores de SPY, QQQ, IWM, XLK y SMH coinciden con los CSV del 30 de septiembre. El caso QQQ 30-OCT-2026 722C coincide con el snapshot del 26 de septiembre: Delta .692946, Gamma .006618, Theta/día -.311769, Vega por punto .796807, IV .233177, mid 34.105. Son valores históricos.

## Desactualizado y faltante

Los archivos tenían prefijo `_`; ahora sus nombres son canónicos. README mezclaba V1/V2 y tenía un conflicto. “Operativa/completado” omitía errores parciales, calidad inválida y falta de tests. Ya existía dealer por expiración legacy, pero sin integración universal consistente. El Enum incluye BOND/OPTION/UNKNOWN, aunque el resolver no detecta todas esas clases y trata símbolos desconocidos como EQUITY. Capabilities no garantizan cobertura del proveedor, especialmente opciones de índices; SPX/NDX/VIX normalizan a símbolos de índices, sin sustituirlos por contratos de ETFs.

Maximum Sharpe existe en módulos legacy; el optimizador universal implementa equal weight, inverse volatility, minimum variance y signal tilted. Enumerar métricas de forecast no acredita validación de todos los modelos/activos/horizontes. Deep Research por ticker no incluye portfolio, riesgo ni Flow.

## Correcciones implementadas

Drawdown incorpora capital inicial; límites por defecto del portfolio son factibles para uno/dos activos; restricciones imposibles fallan explícitamente. Crypto anualiza mercado con 365. Cadenas se validan antes de Greeks/dealer, con rechazos auditables. Greeks respetan DTE fraccional; Vanna analítica y Charm tratan vencimiento. Se excluye 0DTE sin hora fiable. Walls agregan OI por strike; nodos respetan signo y agregación legacy usa solo fecha. Dealer universal por expiración incluye exposiciones, Walls, perfiles y varios Gamma Flips. Deep Research respeta horizonte, usa beta60 y registra procedencia/fallos por etapa. API usa hilos para cálculos y protege el predictor compartido. Dashboard muestra resultados parciales y lee informes guardados. Flow identifica cambios de sesión, falta de base y retrocesos de volumen; rechaza cantidades inválidas y cotizaciones cero no se clasifican BUY.

Ver `documentacion/CAMBIOS_V21.md` para validación. Los informes existentes del 1 de octubre de QQQ/SPY tienen esquema 2 y estado PARCIAL por calidad. Los cinco snapshots originales del 30 de septiembre se reprocesaron aparte, sin sobrescribirlos.

## Deuda y límites

YFinance como único proveedor, frescura bid/ask desconocida, calendarios/hora exacta pendientes, r/q/multiplicador/signo dealer fijos, Flow aproximado, duplicación legacy/universal, signal tilted sin calibración económica y calendarios mixtos de portfolio. Regresión técnica de Kronos no prueba rentabilidad; benchmark QQQ guardado tiene solo seis observaciones por modelo a 20 días. Dashboard carece aún de Options Lab, selector y monitor de trades. Persisten advertencias de dependencias. No se valida aquí trading en vivo ni ejecución de órdenes.

Siguiente trabajo concreto: Expected Move por vencimiento sobre la cadena validada, con estimaciones straddle e IV, procedencia, pruebas e integración en informe/dashboard.
