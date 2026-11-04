# Revisión de interfaces y chat — 2026-11-04

Se revisaron Dashboard, Chat IA, Cuentas, Modelos, Plantillas, Actividad y Configuración, junto con login y rutas API. Auditoría estática: IDs de DOM sin duplicados, todas las referencias el() existen y los handlers de eventos de HTML tienen función JavaScript. CSS incluye breakpoints 1150/900/640px y reduced-motion. Esto no demuestra visualización perfecta en cada tamaño: el navegador de automatización no estuvo disponible (inventario sin navegadores).

## Correcciones publicadas

- El chat deja de contar fragmentos SSE como tokens. Solo usa completion_tokens informado por el servidor; cuando no hay uso real, no muestra TPS inventados.
- Se retiraron de tarjetas y selectores los rangos de TPS no medidos en esta instalación. Permanecen metadatos de arquitectura como descripción, no como benchmark.
- Si la API rechaza imágenes con HTTP400/422, se informa que no hubo análisis visual. No se vuelve a enviar la conversación sin las imágenes silenciosamente.
- Textos del chat e instrucciones al modelo aclaran que los videos/audios se reproducen y descargan, pero no se extrajeron fotogramas ni transcripciones para analizarlos.
- Extracción Office limitada por número de entradas, tamaño descomprimido total y tamaño de XML antes de leerlo. Evita que archivos comprimidos pequeños agoten memoria.
- Parámetros de temperatura/salida y longitud de mensaje se validan antes de guardar mensajes, evitando conversaciones con respuestas fantasma cuando las opciones son inválidas.
- El campo de escritura del chat tiene nombre accesible explícito.

## Verificación

61 pruebas pasan en Windows y Linux; sintaxis JavaScript válida. HTTPS autenticado devolvió200 para raíz, JS/CSS, conversaciones y catálogo; conversaciones anónimas401 y mutación anónima401/403. No se crearon ni borraron conversaciones reales para esta comprobación.

Ambas cuentas Kaggle COMPLETE y puertos18134/17860 sin listeners; servicios de panel siguen activos. No se encendieron GPU ni se hicieron benchmarks o nueva generación real. Se guardó respaldo privado de fuentes previo al despliegue. Exportación pública escaneada contra secretos al cierre.

## Próximas mejoras recomendadas

1. Compacción del contexto por presupuesto de tokens: el límite actual de últimos14 mensajes no controla bien archivos largos ni preserva una memoria resumida.
2. Multimodalidad real verificada: el código actual no implementa extracción de fotogramas ni ASR; poder subir/reproducir un archivo no demuestra interpretación.
3. Cancelación inmediata y recuperación de solicitudes tras reiniciar el panel: hoy se observa cancelación al llegar datos del stream y el estado de solicitudes vive en memoria.
4. Cuota total y retención recuperable de adjuntos en disco, además de los límites por archivo y mensaje.
5. Revisión visual real en escritorio y móvil cuando el navegador esté disponible. No se presenta como realizada en esta entrega.

Investigación oficial y repositorios: KAGGLE_REVISION_20261104.md.
