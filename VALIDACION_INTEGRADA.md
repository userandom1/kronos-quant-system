# Punto 7: validación integrada con datos reales

Fecha: 16 de noviembre de 2026. Rama: `re-design`. Resultado: **aprobado para el alcance actual** de capturas, comparación de cadenas, Delta/Gamma, terminal y Jupyter.

## Recorrido comprobado

1. Captura nueva de QQQ desde `yfinance`, con tres vencimientos, sin usar archivos sintéticos.
2. Validación de contratos y cálculo Delta/Gamma. Los contratos 0DTE sin hora exacta de expiración se conservan en la captura y se omiten del cálculo.
3. Comparación con una captura QQQ anterior del mismo día, guardada por el proyecto. Actividad estimada separada de operaciones individuales.
4. Agregados por strike/vencimiento y escenario dealer opcional. Comprobación de conciliaciones y SHA-256 de todos los archivos del manifiesto.
5. Repetición offline con los archivos guardados y los mismos supuestos; el `informe.json` obtuvo la misma huella.
6. Ejecución del notebook con el informe real y con el filtro del usuario de solo calls y tema oscuro. Diez imágenes quedaron dentro del notebook y se exportaron diez PNG. El escenario dealer se corrigió para respetar el filtro de calls/puts.

## Evidencia local

| Comprobación | Resultado |
| --- | --- |
| Captura real | QQQ, 827 contratos, tres vencimientos, 827 válidos, 0 rechazados |
| Delta/Gamma | 521 calculados; 306 omitidos por `hora_expiracion_desconocida` en 0DTE |
| Procedencia | Spot 661.75 USD, observado a las 21:00 UTC; hora de bid/ask desconocida en 827 contratos |
| Actividad comparada | 771 contratos comparables, 56 sin volumen comparable; incremento total observado 0 |
| Integridad | 15 archivos con SHA-256 correcto; agregados y cobertura conciliados |
| Reproducción offline | SHA-256 del informe `809f11ba3b7c225b28a8a727d7362ca54b885cc526647e7ade8cea0a439d4450` en ambas ejecuciones |
| Notebook real | Diez imágenes embebidas y diez PNG; filtro solo calls y tema oscuro |
| Pruebas automatizadas | 21 pruebas offline aprobadas, incluida detección de un archivo alterado |

Las carpetas locales de esta validación son `resultados/analisis/20261116T232244165110Z_191e2cff/` y `resultados/visualizaciones/validacion_integrada_20261116_final/`. Los datos del proveedor y resultados de análisis se excluyen de Git. El notebook versionado sigue usando el informe sintético para poder abrirlo sin esos datos locales.

Para repetir la comprobación de integridad en la carpeta local:

```powershell
py -3.12 scripts/verificar_ejecucion.py resultados/analisis/20261116T232244165110Z_191e2cff
py -3.12 -m unittest discover -s tests -q
```

## Límites observados

La captura se hizo después del cierre de mercado estadounidense; la comparación no mostró incrementos de volumen. Esto valida el recorrido de captura y comparación, pero no demuestra detección de actividad intradía no nula con datos reales. La hora de bid/ask no está verificada y la descarga no acredita tiempo real. Tasa y dividendo continuos se fijaron en 0 para esta prueba técnica; no son supuestos de valoración recomendados. El escenario dealer es hipotético; no representa posiciones observadas. El proyecto sigue sin un feed de operaciones individuales.
