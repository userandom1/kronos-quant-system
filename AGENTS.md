# Instrucciones de trabajo — rama re-design

Este proyecto se reconstruye por etapas. Antes de implementar un componente, revisar su contrato de datos, sus supuestos y su criterio de aceptación con el usuario. Consultar `PLAN_REDISENO.md` como registro de decisiones.

- Comunicar, documentar y comentar código en español cuando sea razonable.
- Mantener el trabajo del proyecto en `D:\`.
- El núcleo del producto es Options Flow, Delta y Gamma.
- Mostrar resultados numéricos y diagnósticos en terminal.
- Generar resultados gráficos en notebooks Jupyter; cada imagen debe estar junto al código que la genera y ofrecer parámetros visibles para personalizar contenido y presentación.
- No construir dashboards ni interfaces web salvo instrucción nueva y explícita del usuario.
- Distinguir datos observados, cálculos, estimaciones y escenarios de posicionamiento.
- No atribuir dirección de una operación a comparaciones de snapshots ni presentar proxies dealer como posiciones reales.
- Conservar procedencia, tiempos, unidades y motivos de rechazo de datos.
- Añadir pruebas que verifiquen fórmulas, datos inválidos y reproducibilidad cuando se implemente cada módulo.
- El checkout de `quant-platform-v2` y el respaldo previo al rediseño son referencias históricas; no modificarlos durante esta reconstrucción.
