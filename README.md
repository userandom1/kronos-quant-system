# Kronos — rediseño

Nueva plataforma centrada en **Options Flow, Delta y Gamma**. Esta rama empieza desde una base limpia para reconstruir cada componente tras revisarlo.

## Forma de uso acordada

- Datos, tablas, controles de calidad y errores: terminal.
- Gráficas: notebooks Jupyter con el código que genera cada imagen y parámetros visibles para personalizarla.
- Sin dashboard ni interfaz web.
- Diferenciar operaciones individuales observadas de actividad estimada mediante comparaciones de capturas.

El alcance y el orden de reconstrucción están en [PLAN_REDISENO.md](PLAN_REDISENO.md). El sistema analiza capturas guardadas o nuevas desde `yfinance` y genera figuras personalizables en Jupyter.

Las siete etapas, incluida la [validación integrada con datos reales](VALIDACION_INTEGRADA.md), están completadas para el alcance actual.

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

## Análisis completo desde terminal

En Windows, crear el entorno dentro de `D:\02_Herramientas\kronos` e instalar `requirements-live.txt` para captura en vivo. La caché de zona horaria de `yfinance` se dirige a `.cache/` del proyecto. Si `py -3.12` ya dispone de las dependencias, se pueden ejecutar directamente estos ejemplos:

```powershell
# Captura del proveedor, análisis y carpeta nueva bajo resultados/analisis/
py -3.12 -m options_flow analizar --en-vivo QQQ --max-vencimientos 3 --tasa-anual 0 --dividendo-anual 0

# Comparar con la captura actual de una ejecución anterior
py -3.12 -m options_flow analizar --en-vivo QQQ --max-vencimientos 3 --anterior-ejecucion D:\ruta\a\ejecucion_previa --tasa-anual 0 --dividendo-anual 0

# Repetir un análisis sin red desde los archivos guardados
py -3.12 -m options_flow analizar --metadatos D:\ruta\a\ejecucion\actual_metadatos.json --contratos D:\ruta\a\ejecucion\actual_contratos.csv --tasa-anual 0 --dividendo-anual 0

# Incluir el escenario dealer separado de los agregados principales
py -3.12 -m options_flow analizar --metadatos ejemplos/captura_sintetica_2.json --contratos ejemplos/contratos_sinteticos_2.csv --tasa-anual 0.04 --dividendo-anual 0.01 --escenario-dealer
```

Los valores `0` de tasa y dividendo de la demostración son **supuestos de prueba**, no parámetros de mercado recomendados. Se debe pasar ambos explícitamente. El resultado principal separa calls y puts por strike y vencimiento. `Delta×OI×M` y `Gamma×OI×M` describen la hipótesis de mantener largos todos los contratos con OI conocido; no muestran posiciones reales. El escenario dealer opcional usa calls cortas y puts largas y se etiqueta como hipótesis.

Cada ejecución crea una carpeta nueva e incluye las entradas originales, `informe.json`, tablas CSV, `manifiesto.json` y huellas SHA-256. El informe conserva además la huella del código de análisis. Repetir con los mismos archivos, supuestos y código genera la misma huella del informe, aunque la carpeta tenga otro identificador. Los archivos bajo `resultados/` no se suben a Git.

`yfinance` aporta el campo de última operación, que se conserva como tal. No aporta una hora verificable para cada bid/ask; esta queda desconocida y la descarga no certifica tiempo real. Para contratos `REGULAR` se supone multiplicador 100; otros tamaños se rechazan hasta verificar el entregable. Esta distinción sigue la [especificación de opciones estándar y ajustadas de OCC](https://www.theocc.com/clearance-and-settlement/clearing/equity-options-product-specifications). La [API de `yfinance`](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html) se usa para vencimientos y cadenas, sin tratar su resultado como operaciones individuales.

## Figuras en Jupyter

Instala `requirements-notebook.txt` en un entorno Python 3.12 dentro de este proyecto y abre [notebooks/analisis_options_flow.ipynb](notebooks/analisis_options_flow.ipynb). El notebook incluido usa [ejemplos/informe_sintetico.json](ejemplos/informe_sintetico.json), marcado como datos sintéticos; ya contiene seis imágenes ejecutadas y el código que las generó. Selecciona el kernel de ese entorno y ejecuta todas las celdas después de cambiar la segunda celda de configuración.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
```

En `RUTA_INFORME` puedes elegir cualquier `informe.json` de `resultados/analisis/`. `FILTROS` controla vencimientos, calls/puts, strikes y distancia al spot; la vista por vencimiento se vuelve a agregar desde los strikes seleccionados. `ESTILO` permite cambiar tema, colores, tamaño, resolución, fuente, títulos, etiquetas, unidades, límites y escala. `SERIES` permite activar gráficos, líneas, cuadrícula, leyenda y anotaciones. `EXPORTACION` guarda PNG, SVG o PDF cuando `activar=True`; los nombres incorporan una huella del informe y de la configuración para evitar colisiones. La fuente y su SHA-256 aparecen en el notebook. Cada imagen se conserva también como salida de la celda con su código.

Por ejemplo, cambia `ESTILO["tema"]` a `"dark_background"`, `ESTILO["colores"]["CALL"]` a `"#ff46bc"` y `FILTROS["max_strikes"]` a `2`; después ejecuta todas las celdas. Para otra captura, cambia `RUTA_INFORME`. El informe de origen permanece intacto. Los datos numéricos completos siguen disponibles en la terminal y en los CSV de cada ejecución.

También se ha ejecutado localmente el notebook con una comparación de capturas de QQQ en `resultados/visualizaciones/qqq_20261116/analisis_options_flow.ipynb`: produjo cinco imágenes y archivos PNG. Esos resultados locales quedan fuera de Git. Esa comparación no mostró incrementos comparables de volumen; el gráfico lo indica sin atribuir dirección de órdenes.

La versión anterior sigue en la rama `quant-platform-v2`. El checkout original y el respaldo local previo al rediseño conservan también los cambios que no estaban en commits.
