# Kronos — rediseño

Nueva plataforma centrada en **Options Flow, Delta y Gamma**. Esta rama empieza desde una base limpia para reconstruir cada componente tras revisarlo.

## Forma de uso acordada

- Datos, tablas, controles de calidad y errores: terminal.
- Gráficas: notebooks Jupyter con el código que genera cada imagen y parámetros visibles para personalizarla.
- Sin dashboard ni interfaz web.
- Diferenciar operaciones individuales observadas de actividad estimada mediante comparaciones de capturas.

El alcance, el contrato de datos inicial y el orden de reconstrucción están en [PLAN_REDISENO.md](PLAN_REDISENO.md). Aún no hay motor ejecutable en esta rama.

La versión anterior sigue en la rama `quant-platform-v2`. El checkout original y el respaldo local previo al rediseño conservan también los cambios que no estaban en commits.
