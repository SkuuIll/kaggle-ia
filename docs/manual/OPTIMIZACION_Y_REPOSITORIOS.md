# Diagnóstico, Perfiles de Rendimiento y Ahorro de Cuota

## Centro de diagnóstico y control operativo

En **Configuración → Conexión** disponés de tres herramientas para gestionar tus sesiones con precisión:

1. **Diagnosticar conexión:** comprueba en segundos tres capas sin generar texto ni iniciar GPUs:
   - Estado oficial del notebook en Kaggle (`RUNNING`, `QUEUED`, `COMPLETE`, etc.).
   - Respuesta autenticada del endpoint HTTPS (`/inference/cuentaN/v1/models`).
   - Presencia efectiva del modelo cargado en la memoria de Ollama (`/api/ps`).
2. **Preparar para trabajar:** si la cuenta ya está encendida, verifica su disponibilidad; si está apagada, lanza el flujo de arranque verificado asegurando que no haya otra cuenta activa simultáneamente.
3. **Seguir trabajando · +30 min:** extiende en 30 minutos el límite máximo de la sesión activa y renueva el temporizador de inactividad (hasta 4 extensiones por sesión, sujeto a los límites de Kaggle). Requiere que la sesión esté ejecutando el gateway con capacidad `session-v1`.

---

## Etapas de arranque en tiempo real y avisos

Durante el encendido, el notebook informa de forma autenticada a `/api/runtime` el avance real de la máquina:
1. `GPU asignada` (`assigned`)
2. `Instalando servidor` (`install`) — omite `apt`/`pip` si las dependencias ya existen en la imagen.
3. `Descargando pesos` (`download`) — descarga únicamente el archivo GGUF fijado en `/kaggle/temp`.
4. `Registrando modelo` (`register`)
5. `Cargando en GPU` (`warm`) — ejecuta una prueba corta de generación (`Responde LISTO`) con `keep_alive: -1`.
6. `Listo` (`ready`)

> **Importante sobre tiempos y paradas:** Los tiempos de espera en cola de Kaggle (`QUEUED`) no son predecibles, por lo que el panel no inventa cuentas regresivas durante la cola. Asimismo, la etapa `stopped` indica que los procesos internos están cerrándose, pero el panel solo confirma el apagado cuando la API oficial de Kaggle reporta un estado terminal (`COMPLETE`, `CANCEL_ACKNOWLEDGED` o `ERROR`).

Con el panel abierto en el navegador y las notificaciones activadas, el banner muestra el tiempo restante hasta el corte por inactividad y hasta el límite total de la sesión, emitiendo alertas a los 2 minutos de inactividad restante y 5 minutos antes del límite de sesión.

---

## Perfiles de contexto y presupuesto de salida

Podés ajustar el perfil de cada cuenta para su próximo arranque sin cambiar de modelo:

| Perfil | Contexto (`num_ctx`) | Salida máxima (`output_tokens`) | Caso de uso recomendado |
|---|---:|---:|---|
| **Respuesta rápida** | `16.384` | `1.024` | Consultas puntuales, autocompletado y ediciones breves |
| **Código** | `32.768` | `4.096` | Desarrollo cotidiano trabajando con varios archivos |
| **Contexto largo** | `131.072` | `4.096` | Análisis de módulos extensos o refactorizaciones grandes |

Reducir el contexto disminuye el uso de VRAM (KV cache) y el tiempo de preprocesamiento de prompts largos. Tras cambiar de perfil, volvé a copiar o descargar la configuración de tus clientes para sincronizar los límites de `contextLength` y `maxTokens`.

---

## Optimización de TPS para las GPUs de Google/Kaggle (2× NVIDIA Tesla T4)

Cuando el notebook solicita `machine_shape: "NvidiaTeslaT4"`, Kaggle asigna **2 GPUs NVIDIA Tesla T4** (arquitectura Turing `sm_75`, **16 GB GDDR6 cada una = 32 GB totales** y **320 GB/s** de ancho de banda de memoria por placa).

Dado que la generación token a token (`batch_size = 1`) está limitada por el **ancho de banda de memoria VRAM**, el proyecto aplica tres optimizaciones clave:

1. **Arquitectura Mixture-of-Experts (`MoE A3B`) y Multi-Token Prediction (`MTP`):**
   - Un modelo denso de 27B (`16,8 GB`) obliga a leer los 16,8 GB completos a través del bus PCIe por cada token generado (**~12–18 TPS**).
   - En cambio, los modelos **MoE A3B** (`Qwen3 Coder 30B A3B`, `Cyber-Tiel 35B A3B · MTP`, `Qwen3.6 35B A3B · MTP`) alojan 30B–35B parámetros en las dos T4 pero **solo activan ~3B parámetros (~2 GB) por token**, alcanzando **45 a 65 TPS** con calidad de un modelo de 30B+.
2. **Modelos de 1 sola GPU (`7B` a `14B`):**
   - Modelos de menos de 10 GB (`Qwen3.5 9B`, `Qwen2.5 Coder 14B`, `Qwen2.5 Coder 7B`) caben íntegros dentro de los 16 GB de la primera Tesla T4 sin dividir capas por PCIe y se descargan en ~1 minuto.
3. **FlashAttention-2 y caché KV cuantizada (`Q8_0`):**
   - `sistema/build_single_notebook.py` activa `OLLAMA_FLASH_ATTENTION=1` y `OLLAMA_KV_CACHE_TYPE=q8_0`, reduciendo a la mitad el consumo de VRAM y el ancho de banda leído por la caché de contexto sin degradar la calidad de código.

---

## Prácticas para ahorrar horas de GPU en Kaggle

- **Apagado confirmado al terminar:** toda sesión `RUNNING` en Kaggle descuenta cuota (incluso durante la descarga de pesos o si no estás enviando mensajes). Cerrar el navegador, el IDE o la PC **no detiene Kaggle**: usá siempre el botón **Apagar** o **Apagar todas** del panel.
- **Equilibrio en el autoapagado:** la política por defecto es de **15 minutos de inactividad** y **120 minutos de sesión máxima**. No configures tiempos de inactividad excesivamente bajos (ej. 1–2 minutos), ya que obligarían a reiniciar y volver a descargar el modelo repetidamente, gastando más cuota en arranques en frío.
- **Sondeo pasivo:** las consultas periódicas de estado del panel y el botón de diagnóstico no envían prompts al modelo ni reinician el contador de inactividad.

---

## Referencias de arquitectura evaluadas

| Proyecto de referencia | Aporte analizado | Adopción en Kaggle IA |
|---|---|---|
| [Nasus20202/KaggleInferenceServer](https://github.com/Nasus20202/KaggleInferenceServer) | API compatible con OpenAI y proxy de inferencia | Se mantiene nuestra arquitectura de túnel SSH restringido y proxy HTTPS con autenticación Bearer por cuenta. |
| [Shreyash-Gaur/ShadowGPU](https://github.com/Shreyash-Gaur/ShadowGPU) | Control explícito de ciclo de vida y residencia en VRAM | Se adoptan controles explícitos de estado, extensión de sesión y verificación de modelo residente (`keep_alive: -1`). |
| [Tahsine/kaggle-llm-server](https://github.com/Tahsine/kaggle-llm-server) | Separación entre preparación de pesos y ejecución GPU | Oportunidad futura: precargar pesos GGUF en un Dataset privado de Kaggle desde CPU para reducir el tiempo de descarga al iniciar la GPU. |
| [Kaggle: Efficient GPU Usage](https://www.kaggle.com/docs/efficient-gpu-usage) | Documentación oficial de cuotas y sesiones | Consulta directa de `get_accelerator_quota_statistics` en lugar de estimar cuotas fijas. |
