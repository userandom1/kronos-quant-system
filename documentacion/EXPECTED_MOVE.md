# Expected Move por vencimiento

Integrado el 3 de octubre de 2026 en Deep Research, auditoría histórica y Dashboard V2. Módulo: `motor_opciones/movimiento_esperado.py`. No depende de Kronos ni necesita descargar datos cuando recibe una cadena guardada.

## Métodos y unidades

- **Straddle ATM:** `(bid_call + ask_call)/2 + (bid_put + ask_put)/2`. Se usa la prima completa, sin factores heurísticos adicionales. Es una referencia de movimiento basada en prima; no se le asigna una probabilidad.
- **IV ATM:** `spot × ((IV_call + IV_put)/2) × sqrt(DTE/365)`. IV decimal anualizada; DTE calendario, incluido fraccional positivo. Es una aproximación de escala de volatilidad, no una probabilidad calibrada.
- Movimiento en dólares por unidad del subyacente y porcentaje respecto al spot. No multiplica por 100 como una prima de contrato.
- Ambos intervalos se centran en el spot: `[spot - movimiento, spot + movimiento]`. Los breakevens de un straddle comprado se centrarían en el strike y dependen de prima/costes; son conceptos distintos.
- La aproximación simétrica puede producir límites negativos con IV/DTE extremos; no se recortan para ocultar ese límite del método. No representa una distribución calibrada de precios ni garantías.

Referencias primarias: [CME, volatilidad y escala con raíz del tiempo](https://www.cmegroup.com/education/courses/introduction-to-options/discover-options-volatility) y [Options Industry Council, estructura del straddle](https://prd-web.optionseducation.org/strategies/all-strategies/long-straddle). La media de IV call/put, base 365 y distancia ATM son convenciones explícitas de esta implementación.

## Selección y calidad

Una pareja usa la misma fecha normalizada y el mismo strike, con una call y una put válidas. Se selecciona el strike original más próximo al spot; empate: menor strike. Distancia máxima ATM por defecto: 2%, configurable mediante `PoliticaMovimientoEsperado`. No se sustituye una pareja incompleta por otra más lejana.

Se aplican los controles compartidos de `calidad_cadena.py`: datos finitos, strike/ask positivos, bid no negativo, mercado no cruzado, spread relativo máximo 100%, IV entre .0001 y 5, DTE positivo, OI no negativo, fecha/tipo válidos y deduplicación. El mid se recalcula desde bid/ask. Las fechas equivalentes se normalizan antes de deduplicar. DTE de call/put debe coincidir dentro de 1e-6 días.

Los rechazos originales se incorporan para reconocer la ausencia de la pareja ATM. En Deep Research se leen del CSV de rechazos; en la auditoría se evalúa la cadena original. Si una fuente ya filtrada no conserva sus rechazos, no puede reconstruirse una selección ATM eliminada por completo.

Estados por vencimiento: `OK`, `SIN_CONTRATOS_VALIDOS`, `SIN_PAREJA_ATM`, `ATM_LEJANO` y `DTE_INCONSISTENTE`. Los estados sin estimación guardan valores nulos, no movimiento cero. Fechas inválidas se cuentan en la auditoría de calidad, pero no generan una expiración ficticia. 0DTE sin tiempo fiable sigue excluido. Los motivos de fallo quedan visibles.

Se conservan strike, spot, DTE, mid, IV de ambos lados/media, spreads, símbolos de contratos cuando existen, recuentos de calidad, fórmulas y base temporal. La antigüedad de las cotizaciones sigue **NO_VERIFICADA**; calidad técnica no certifica ejecutabilidad ni contemporaneidad de call y put.

## Uso e integración

```powershell
.venv\Scripts\python.exe -m motor_sistema.deep_research QQQ 20 --modelos DRIFT MOMENTUM
.venv\Scripts\python.exe -m herramientas.reprocesar_deep_research --fecha 20260930
.venv\Scripts\python.exe -m herramientas.verificar_proyecto
```

Deep Research añade `expected_move_por_vencimiento.csv` y el campo JSON `expected_move_por_vencimiento`. La etapa tiene estado independiente; una expiración sin estimación implica PARCIAL y un fallo no oculta el dealer. Activos sin opciones marcan NO_COMPATIBLE; fallos de opciones bloquean la etapa. Se conserva compatibilidad del esquema 2 mediante campos adicionales.

La auditoría exporta las mismas estimaciones y conserva DTE/spot del snapshot. En Dashboard V2: analizar un activo → **Ver último Deep Research guardado** → **Expected Move por vencimiento**. Cada expiración despliega los dos métodos, intervalos y calidad. Los informes antiguos con cadena se recalculan en memoria al leer la API, con procedencia explícita, sin escribir sobre el informe. Una fecha de snapshot no convierte los datos en cotizaciones actuales. Si no existe cadena o hay error, la interfaz lo explica.

## Validación

Suite completa: 68 pruebas pasadas, con 15 advertencias de dependencias ya conocidas. Se validan fórmulas/porcentajes, límites, raíz del tiempo, DTE fraccional, parejas incompletas, strike/fecha comunes, exclusiones, distancia ATM, duplicados/formatos de fecha, spot inválido, CSV/JSON, independencia de etapas y compatibilidad sin escritura de informes antiguos.

Auditoría de cinco snapshots del 30 de septiembre: 51 de 60 expiraciones con estimación; nueve identificadas sin estimación. Salida: `resultados/auditoria_v21/20261003_095034_649642/`.

| Activo | Expiraciones con estimación | Sin estimación |
|---|---:|---:|
| SPY | 11 | 1 |
| QQQ | 11 | 1 |
| IWM | 11 | 1 |
| XLK | 8 | 4 |
| SMH | 10 | 2 |

Verificación visual con el último informe QQQ disponible: métodos e intervalos por fecha, comparación de prima e IV, recuentos y procedencia histórica. Screenshot local: `.cache/verificacion_ui/expected_move_qqq.jpg`. No se ha probado utilidad predictiva ni cobertura probabilística; eso exige seguimiento fuera de muestra.
