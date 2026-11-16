# Kronos — rediseño

Nueva plataforma centrada en **Options Flow, Delta y Gamma**. Esta rama empieza desde una base limpia para reconstruir cada componente tras revisarlo.

## Forma de uso acordada

- Datos, tablas, controles de calidad y errores: terminal.
- Gráficas: notebooks Jupyter con el código que genera cada imagen y parámetros visibles para personalizarla.
- Sin dashboard ni interfaz web.
- Diferenciar operaciones individuales observadas de actividad estimada mediante comparaciones de capturas.

El alcance, el contrato de datos inicial y el orden de reconstrucción están en [PLAN_REDISENO.md](PLAN_REDISENO.md). La primera etapa acepta capturas guardadas; todavía no calcula Delta ni Gamma.

## Validar una captura

Los archivos de `ejemplos/` son **sintéticos**, no datos de mercado. El JSON identifica la captura y el CSV contiene los contratos. Se necesita Python 3.12 o posterior.

```powershell
py -3.12 -m options_flow ejemplos/captura_sintetica.json ejemplos/contratos_sinteticos.csv
py -3.12 -m options_flow griegas ejemplos/captura_sintetica.json ejemplos/contratos_sinteticos.csv --tasa-anual 0.04 --dividendo-anual 0.01
py -3.12 -m unittest discover -s tests -v
```

El comando conserva los archivos de entrada, muestra motivos de rechazo por línea y calcula SHA-256 de ambos archivos. Un contrato con vencimiento el mismo día y sin hora exacta permanece en la captura, pero queda marcado como no apto para calcular Greeks.

La **fecha de vencimiento es obligatoria**. La hora puede faltar: para fechas futuras se usan días naturales completos y se etiqueta el resultado `DIAS_CALENDARIO`; en 0DTE no se calculan Greeks sin hora exacta. Tasa y dividendo anual continuo se indican explícitamente en el comando; no hay valores predeterminados. Delta y Gamma son por unidad del subyacente, antes de aplicar el multiplicador del contrato.

## Fórmula y alcance

El cálculo usa Black-Scholes-Merton europeo con rendimiento continuo por dividendos `q`:

```text
d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
Delta call = e^(-qT) N(d1)
Delta put  = e^(-qT) [N(d1) - 1]
Gamma     = e^(-qT) φ(d1) / (S σ√T)
```

`T` se expresa en años de 365 días. Si existe hora de expiración, se calcula con segundos; de lo contrario, solo para fechas futuras, se usan días naturales completos y se muestra esa precisión. El modelo europeo aproxima contratos americanos y no verifica por sí solo la actualidad de bid/ask o IV. Bases teóricas: [Black y Scholes (1973)](https://www.journals.uchicago.edu/doi/10.1086/260062) y [Merton (1973)](https://ideas.repec.org/a/rje/bellje/v4y1973ispringp141-183.html).

La captura histórica `snapshot_20260925_105333.csv` del proyecto anterior no incluye una hora UTC verificada de captura ni de cotización. No se importará como captura nueva inventando esas horas; se revisará su migración como dato histórico separado.

La versión anterior sigue en la rama `quant-platform-v2`. El checkout original y el respaldo local previo al rediseño conservan también los cambios que no estaban en commits.
