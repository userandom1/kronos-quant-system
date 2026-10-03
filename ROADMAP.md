# Quant Platform — prioridades verificables

Actualizado el 3 de octubre de 2026. Roadmap original conservado en documentacion/historico/ROADMAP_20260930.md. Priorizar utilidad, robustez y validación.

## Base entregada

V2.0 universal está implementada, con límites de clasificación/cobertura. V2.1 Deep Research está integrada y estabilizada: estados parciales, calidad, Greeks, gráficas, escenarios, trazabilidad y pruebas. No equivale a certificar datos ni modelos.

La base de Dealer por expiración de V2.2 está integrada: GEX/DEX/Vega/Vanna/Charm, Walls y perfiles/cruces Gamma por fecha, con lectura desde Dashboard V2. Pendientes tasas/dividendos/multiplicadores configurables, calendario/frescura y contraste externo. Sigue siendo proxy.

## Expected Move — implementado e integrado

1. Seleccionar call/put ATM del mismo strike/expiry en la cadena validada; informar falta de pareja o spread excesivo.
2. Calcular straddle y aproximación spot × IV × sqrt(DTE/365), conservando ambos métodos con unidades explícitas.
3. Guardar límites superior/inferior, move en dólares/porcentaje, DTE, IV y procedencia. No presentar automáticamente straddle como intervalo de confianza.
4. Probar fórmulas, fechas, cadenas incompletas y calidad.
5. CSV/JSON integrados en Deep Research y auditoría; dashboard muestra ambos métodos por vencimiento.

Validación: 68 pruebas globales pasadas y cinco snapshots históricos auditados (51 expiraciones con estimación, nueve sin ella). Ver documentacion/EXPECTED_MOVE.md.

Próxima entrega funcional: IV Term Structure y Skew; la frescura/calendarios de cotización siguen siendo una prioridad transversal.

## Después

| Prioridad | Trabajo | Condición de entrega |
|---|---|---|
| Alta | Frescura/calendarios/convenciones | Timestamps fiables, metadata y reproducibilidad |
| Alta | Term structure y skew | ATM/25Δ, risk reversal/butterfly, interpolación explícita |
| Alta | Contract Selector | Delta/DTE/IV/spread/OI/premium; comparador cuantitativo |
| Alta | ROI de escenarios | P&L/premium inicial; unidades y costes |
| Alta | Forecast validation | Walk-forward amplio, baselines, intervalos y regímenes |
| Media | Trade Monitor y paper journal | Entradas persistentes y P&L trazable |
| Media | Greek P&L attribution | Delta/Gamma/Theta/Vega y residual coherente |
| Media | Deep Research de riesgo | Flow, riesgo y comparador multi-activo |
| Media | Dashboard avanzado | Options Lab, portfolio y monitor con pruebas UI |
| Media | Portfolio/riesgo | Calibrar señales, calendarios mixtos, factores y shocks |
| Progresiva | Reducir duplicación legacy | Interfaces/adaptadores sin romper comandos históricos |
| Futura | Multi-provider/tiempo real | Selección por cobertura/calidad/coste |

V2.3–V3.0 son objetivos, no versiones entregadas. Regresión técnica de Kronos no demuestra valor económico. Una feature necesita funcionamiento, pruebas, interpretación, compatibilidad, documentación e integración.
