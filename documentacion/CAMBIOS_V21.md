# Auditoría y estabilización de Quant Platform

Entrega local del 2 de octubre de 2026. Se contrastaron los tres documentos completos, la estructura real, las ramas, los tests y los resultados. Se conservaron los documentos recibidos y los README de ambos lados de la fusión en `documentacion/historico/`. Los snapshots originales no se sobrescribieron.

## Hallazgos y cambios

| Problema detectado | Corrección |
|---|---|
| README en conflicto y documentación mezclada V1/V2 | README consolidado; AGENTS/ESTADO_PROYECTO/ROADMAP canónicos y contrastados |
| Maximum Drawdown omitía el capital inicial | Serie de equity con referencia inicial 1; dos pérdidas del 10% producen -19% |
| Límite por defecto .35 imposible con uno/dos activos | Límite factible por tamaño; restricciones explícitas inviables se rechazan |
| Crypto anualizada de manera distinta en mercado/portfolio | Mercado usa 365; demás clases conservan 252 |
| Datos inválidos entraban en Greeks/dealer | Política de calidad explícita, motivos de rechazo, CSV/JSON auditables |
| DTE menor de un día se convertía artificialmente en un día | DTE fraccional respetado; 0DTE sin hora fiable se excluye |
| Vanna/Charm aproximadas sin tratamiento adecuado al vencimiento | Vanna analítica por punto IV; Charm como cambio de Delta en un día, con payoff terminal |
| Wall elegía el mayor contrato individual | OI sumado por strike/tipo; lado sin OI devuelve ausencia de nivel |
| Nodo Gamma podía tener signo incorrecto | Nodos positivo/negativo requieren ese signo |
| Agregación legacy agrupaba fecha y DTE fraccional | Una fila por fecha de expiración |
| Dealer por expiración disperso en legacy | Módulo universal con exposiciones, Walls, perfiles y Gamma Flips múltiples |
| Deep Research ignoraba horizonte y usaba clave beta incorrecta | Horizonte explícito o 5/20/60 por defecto; beta60 y correlacion60 |
| Fallos internos quedaban ocultos | Estados por etapa OK/PARCIAL/ERROR/BLOQUEADO, logging, errores y cobertura en JSON |
| Un modelo defectuoso interrumpía todo forecast | Modelos sanos conservados; errores registrados; all-failed falla explícitamente |
| Cálculos bloqueaban el bucle async de la API | Rutas síncronas en threadpool y lock del predictor compartido |
| Dashboard ocultaba problemas internos | Mensajes parciales, escape de textos y lectura de informes JSON guardados |
| Flow comparaba volumen acumulado entre días y contratos sin base | Timestamp UTC; sesión Nueva York; nuevo día usa volumen diario; sin base no inventa incremento intradía |
| Capturas invertidas/cantidades inválidas/cotizaciones cero | Validación de orden y cantidades, flags de retroceso y ejecución DESCONOCIDA |
| Dependencias de la plataforma y pruebas ausentes de requirements | Versiones directas del entorno documentadas, requirements-dev y runner offline en D: |

El dealer conserva la convención calls short/puts long y multiplicador 100. Su Gamma Flip revalúa Black-Scholes con IV fija sobre ±20% del spot, 161 puntos; refina cruces con brentq, conserva varios y distingue SIN_CRUCE/SIN_EXPOSICION. No garantiza detectar raíces fuera de la malla o entre puntos cercanos. Los totales por expiración reconcilian las exposiciones de la cadena validada.

## Validación realizada

- Suite completa: **47 pruebas pasadas**, 15 advertencias de deprecación de Matplotlib/Pyparsing y Starlette/AnyIO. Incluye cuatro regresiones Kronos con pesos cacheados y CPU, diez pruebas matemáticas legacy de Greeks y 33 pruebas de estabilización.
- Comando reproducible: `.venv\Scripts\python.exe -m herramientas.verificar_proyecto`. Puede omitirse inferencia con `--sin-modelos`; los pesos deben existir para la suite completa. No se alteraron los valores esperados de las regresiones.
- Sintaxis: 198 archivos Python analizados; JavaScript validado con `node --check`.
- Dependencias: `pip check` sin conflictos; CLI Deep Research `--help` válida; imágenes del README existentes.
- API con TestClient: health 200/operativo; lectura real de informes QQQ/SPY esquema 2, PARCIAL, 11 expiraciones cada uno. IWM/XLK/SMH históricos carecen de informe.json y devuelven 404 hasta una nueva ejecución. La interfaz no convierte CSV legacy silenciosamente en informes nuevos.
- Concurrencia: la prueba comprueba que health responde durante un análisis lento; errores de horizonte se devuelven con HTTP 400. No se afirma haber realizado pruebas visuales completas del navegador.
- El sandbox Windows bloqueó inicialmente temporales de unittest; la suite se ejecutó fuera de ese aislamiento con TEMP/TMP/cachés dentro del proyecto. No se modificaron tests para ocultar el bloqueo.

## Reprocesado histórico sin red

Herramienta: `python -m herramientas.reprocesar_deep_research --fecha 20260930`. Salida validada: `resultados/auditoria_v21/20261002_160700_197177/`. Conserva spot y DTE originales y genera cadenas válidas/rechazadas, perfiles, resumen por expiry y auditoria.json con revisión del código.

| Activo | Contratos originales | Válidos | Rechazados | Expiraciones válidas | Cruces Gamma detectados | Call Wall | Put Wall |
|---|---:|---:|---:|---:|---:|---:|---:|
| SPY | 3486 | 2631 | 855 | 11 | 12 | 785 | 525 |
| QQQ | 3503 | 2663 | 840 | 11 | 12 | 760 | 700 |
| IWM | 1575 | 1154 | 421 | 11 | 17 | 290 | 275 |
| XLK | 1422 | 942 | 480 | 12 | 12 | 200 | 175 |
| SMH | 1560 | 1026 | 534 | 11 | 16 | 700 | 530 |

Total: 11.546 contratos, 8.416 aceptados y 3.130 descartados. Los motivos pueden solaparse: DTE, IV, cotizaciones, spread o duplicados. Los cinco activos reconcilian GEX/DEX/Vega/Vanna/Charm agregado con la suma por expiración. La diferencia con los números originales refleja tanto filtrado como corrección de métricas; no es un cambio observado de mercado. En XLK el Call Wall original 150 correspondía a un contrato individual, mientras el OI agregado selecciona 200. También se ejecutó auditoría sobre las últimas cadenas disponibles en `20261002_160620_732267/`; SPY/QQQ ya estaban filtradas, por lo que no se confunden sus cuentas con el snapshot original.

## Lo que sigue pendiente

1. Frescura real de bid/ask, calendario y hora de expiración. La fecha de captura no certifica la hora de cotización.
2. Proveedor alternativo y capacidades contrastadas por instrumento; opciones de índices pueden no estar disponibles en YFinance. El resolver no cubre todas las clases del Enum.
3. Tasas, dividendos, multiplicadores y convenciones dealer configurables; valoración adecuada de opciones americanas y superficies interpoladas.
4. Calibración económica de signal tilted y revisión de anualización/calendarios en carteras mixtas.
5. Walk-forward representativo de forecasting: seis observaciones QQQ por modelo/horizonte en el benchmark existente son insuficientes para concluir valor incremental.
6. Flow sigue siendo proxy sin feed de operaciones; OI no representa cambios intradía observados. Snapshots antiguos sin timestamps no tienen sesión verificada.
7. Unificación gradual de módulos legacy/universales e integración de riesgo/Flow en Deep Research; Options Lab, selector y monitor aún pendientes.
8. Instalación limpia y CI portable; requirements recoge el entorno verificado, no una matriz certificada de sistemas/GPU.

Siguiente trabajo concreto: Expected Move por vencimiento con straddle e IV, controles de pares ATM, unidades/procedencia y pruebas, integrado en CSV/JSON y dashboard. El alcance de esta entrega es estabilización y dealer por expiración; no declara completado todo el roadmap.
