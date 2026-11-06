# Qwen3.8 Heretic con ExLlamaV3 y DFlash2

El perfil EXL3 sirve el Qwen3.8-27B Heretic ARA de Honkware en dos Tesla T4 de Kaggle. Usa una ventana de 131.072 tokens, caché de 4 bits y borradores DFlash2 de hasta siete tokens. El backend TabbyAPI escucha solo en loopback en el notebook. El relay SSH y la autenticación HTTPS siguen a cargo de la instalación existente.

## Activación y uso

1. Con la GPU del perfil detenida, hacé una copia privada de `sistema/model_profiles.json`. En el perfil de la cuenta que vas a probar, agregá `"engine": "exl3"`, configurá `"context": 131072` y dejá `"source": null`. Conservá el identificador `model` para que el panel y los IDE sigan usando el mismo alias.
2. Desde **Cuentas**, encendé ese perfil y esperá **LISTO**. El notebook instala el runtime y descarga los dos checkpoints en el almacenamiento temporal de Kaggle. Se requiere cuota GPU libre e Internet en el notebook.
3. En **Chat IA → Opciones → Ajustes del chat**, elegí **Directo**, **Breve**, **Medio** o **Profundo**. La preferencia queda en el navegador. Para OpenAI-compatible usá `reasoning_effort` con `none`, `low`, `medium` o `xhigh`.
4. Verificá que el cliente reciba texto real y, si lo usás como agente, que pueda ejecutar una llamada de herramienta. El perfil está orientado a texto. Para análisis de imágenes o video por el auxiliar, usá un perfil Ollama.

Para volver a Ollama, detenés el perfil, esperás la confirmación de Kaggle, quitás `engine` y encendés de nuevo. La selección del motor vive en el catálogo privado. El historial del chat se guarda en la VPS.

## Referencia de rendimiento

Los ensayos de inferencia directa en dos T4 compararon Heretic EXL3 + DFlash2 con RVN + Ollama. En código corto la mediana fue 49,2 frente a 21,1 tokens/s. A 98.986 tokens de entrada en frío, la espera hasta el primer texto fue 293 frente a 543 segundos. En un seguimiento con el mismo prefijo, EXL3 reutilizó 98.816 tokens y comenzó a responder en 1,24 segundos. Ambas configuraciones recuperaron los tres datos de la prueba. Esas cifras pertenecen al benchmark directo y sirven como referencia para medir el panel y la API tras desplegar.

- [Checkpoint Heretic](https://huggingface.co/Honkware/Qwen3.8-27B-heretic-ara-exl3-4.0bpw)
- [Borrador DFlash2](https://huggingface.co/r0b0tlab/Qwen3.8-27B-DFlash2-EXL3-4.00bpw)
- [TabbyAPI](https://github.com/theroyallab/tabbyAPI)
