# Investigación Kaggle y prioridades de integración — 2026-11-04

Fuentes primarias revisadas:

- https://www.kaggle.com/docs/efficient-gpu-usage : cuota semanal y supervisión de sesiones. La cuota depende de recursos/demanda; consultar valor oficial por cuenta, sin fijar una promesa de horas.
- https://github.com/Kaggle/kaggle-api : mantener el SDK/CLI oficial y consultar estado real. Antes de adoptar un endpoint de cancelación, validar su contrato y los identificadores; no equiparar versión del notebook con ID de sesión.
- https://github.com/Kaggle/docker-python : imagen CPU/GPU oficial del entorno. Registrar versión del runtime, CUDA, motor y dependencias en el diagnóstico permite explicar regresiones tras cambios de imagen.
- https://github.com/Tahsine/kaggle-llm-server : separación entre preparación persistente de pesos/binarios y arranque de inferencia. Usar como referencia, conservando SSH privado y las claves propias.

Mejoras recomendadas, sujetas a implementación y validación:

1. Preparar pesos con CPU y almacenarlos en dataset privado, fijando revisión y comprobación de integridad; montar en el notebook GPU evita repetir descarga externa. No afirmar ahorro medido ni caché instalada sin crear y probar el dataset.
2. Registrar perfil real de GPU, memoria, versión de Ollama y tiempo por etapa. Comparar TPS solamente con contadores de tokens informados por el motor: fragmentos SSE no equivalen a tokens.
3. Reservar contexto/salida por tarea y compactar historial del chat: enviar todas las conversaciones o adjuntos repetidamente aumenta tiempo de procesamiento y riesgo de exceder contexto.
4. Reflejar capacidades reales de imágenes/video/audio por modelo. Reintentar sin una imagen no constituye análisis visual; guardar un video no significa interpretar sus fotogramas.
5. Mantener supervisión de tiempo e inactividad, límite de sesión y parada confirmada. Un proceso residente o VRAM ocupada sigue consumiendo la asignación; consultar estado no debe reiniciar el contador de actividad.

No se encendió GPU para esta investigación. Las cifras de TPS de otros repositorios no son mediciones de estas cuentas. No se copian mecanismos para eludir cuotas, ni se reemplaza el relay por un túnel efímero.
