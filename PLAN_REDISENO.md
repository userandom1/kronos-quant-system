# Rediseño de Kronos: Options Flow, Delta y Gamma

Estado: base limpia creada; contrato de datos propuesto para la siguiente revisión.
Rama de trabajo: `re-design`. El proyecto anterior permanece en `quant-platform-v2` y en el respaldo local previo al rediseño.

## Producto y forma de uso

El sistema analiza actividad de opciones y sensibilidad Delta/Gamma de contratos y agregados. Los datos numéricos, controles de calidad, advertencias y errores se consultan desde la terminal. Las figuras se generan en notebooks Jupyter: cada figura aparece junto a la celda de código que la produjo y se puede volver a generar con otros ajustes visuales. No se construirá un dashboard ni una interfaz web.

## Requisito permanente de las figuras

**Todas las respuestas gráficas deben ser personalizables por el usuario.** Ninguna figura final dependerá de colores, tamaños, filtros o disposición fijados dentro de una función sin una opción para cambiarlos.

Cada notebook de análisis tendrá un bloque de parámetros visible antes de las figuras. Como mínimo permitirá cambiar:

- activo, captura, vencimientos, strikes y rango de precios mostrados;
- tema, paleta, colores de calls/puts y exposiciones positivas/negativas;
- dimensiones, resolución, tipografía, títulos, etiquetas, unidades y formato numérico;
- series, niveles, anotaciones, leyenda, cuadrícula y escala de los ejes;
- ruta y formato de exportación de la imagen.

Los parámetros que cambian el cálculo o filtran contratos se distinguirán de los que solo cambian la presentación. El notebook conservará la procedencia de los datos y la configuración usada en cada figura. La imagen quedará visible como salida de su celda; se podrá exportar también como archivo independiente. Personalizar una figura no alterará los datos de origen.

## Distinción de fuentes

1. **Cadena de opciones:** cotizaciones, volumen acumulado, open interest, IV y metadatos de contratos en un instante de captura.
2. **Comparación de capturas:** cambios observados entre dos cadenas compatibles. Es una estimación de actividad; no identifica operaciones individuales ni la dirección real de cada orden.
3. **Operaciones individuales:** flujo de ejecuciones solo cuando exista una fuente que aporte registros, hora, tamaño y precio suficientes. Se conservará separado de la comparación de capturas.

Los informes identificarán el tipo de entrada y la hora de captura. No se presentará un proxy de compra/venta ni una convención de posicionamiento dealer como hecho observado.

## Primer contrato de datos propuesto

Una captura consta de metadatos comunes y filas de contratos. Los metadatos incluyen `id_captura`, activo subyacente, proveedor, `capturado_en_utc`, spot, moneda, fuente y hora del spot, zona horaria de mercado, versión del esquema y archivo original. Si el proveedor no informa la hora de una cotización, se registra como **desconocida**; la hora de descarga no la sustituye.

Cada contrato conserva `id_contrato`, tipo `CALL`/`PUT`, strike, vencimiento, multiplicador, bid, ask, IV, volumen acumulado y open interest. La fecha de vencimiento y la hora exacta de expiración son campos distintos. Los campos numéricos usan unidades declaradas: IV decimal, primas por acción o unidad de contrato, volumen y OI en contratos. El identificador del proveedor y el contrato normalizado se conservan por separado para detectar colisiones o cambios de símbolo.

La validación devuelve tres salidas: contratos válidos, contratos rechazados con todos sus motivos y resumen de cobertura. No convierte ausencias en ceros ni inventa IV, cotizaciones o tiempo hasta expiración. Si no se conoce la hora de expiración de un contrato 0DTE, no se calcularán Greeks para él. Los cálculos guardarán spot, IV, tiempo, tasa, dividendo, fórmula y multiplicador usados.

Una operación individual, cuando exista ese dato, tendrá un esquema aparte: identificador, contrato, hora de ejecución UTC, precio, tamaño, mercado/fuente y, solo si la fuente lo permite, clasificación de agresor y método de clasificación. Una comparación de capturas nunca se transformará en filas de operaciones individuales.

## Primer recorrido funcional propuesto

1. Importar una cadena guardada o capturar una nueva, con proveedor y hora explícitos.
2. Validar identidad del contrato, vencimiento, spot, bid/ask, IV, volumen y open interest. Conservar contratos rechazados y motivos.
3. Calcular Delta y Gamma por contrato con fórmula, supuestos, unidades y política de vencimiento documentados.
4. Agregar Delta/Gamma por strike, vencimiento y tipo; mostrar por separado exposición sin signo de dealer y escenarios de signo asumido.
5. Comparar dos capturas compatibles para estimar cambios de volumen/IV/OI, con controles de sesión y casos sin base anterior.
6. Mostrar tablas y avisos en terminal; guardar datos procesados y metadatos para reproducir el análisis.
7. Abrir un notebook que lea esos resultados y genere figuras Delta/Gamma y actividad de opciones mediante celdas configurables.

## Orden de reconstrucción y revisión

| Etapa | Entrega revisable | Condición para continuar |
| --- | --- | --- |
| 1. Contratos de datos | Esquema de cadena, capturas y operaciones; procedencia y calidad | Ejemplos reales e inválidos se clasifican correctamente |
| 2. Delta y Gamma | Cálculos por contrato, unidades, supuestos y pruebas | Fórmulas y casos límite contrastados |
| 3. Agregados | Tablas por strike y vencimiento; escenarios de exposición | Totales reconcilian con contratos válidos |
| 4. Actividad | Comparación de capturas; importación de operaciones cuando haya fuente | Ningún proxy se etiqueta como operación observada |
| 5. Terminal | Comandos, tablas, errores y archivos de salida | Análisis repetible desde una captura guardada |
| 6. Jupyter | Figuras parametrizadas con código y salida visible | Cada figura se puede personalizar y regenerar |

La primera revisión será el **contrato de datos**, antes de vaciar los módulos heredados de la nueva rama.

## Límites de la propuesta

El código actual dispone de comparaciones de snapshots, Greeks y exposiciones dealer aproximadas. No dispone de un feed verificado de operaciones individuales. La primera versión podrá trabajar con cadenas y capturas guardadas; el flujo de ejecuciones reales quedará condicionado a disponer de datos adecuados. La calidad de bid/ask y la hora exacta de expiración requieren verificación por fuente.
