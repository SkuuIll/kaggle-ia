# Mejoras aplicadas — 2026-11-04

## Chat y contexto

El envío al modelo usa un presupuesto que reserva salida y margen. Para el texto se usa una cota conservadora basada en bytes UTF-8; para imágenes una estimación fija. No es el tokenizador exacto del modelo. Se conservan mensajes recientes completos que quepan; si hay margen se incluyen fragmentos anteriores identificados explícitamente como memoria extractiva parcial. El historial original en SQLite permanece completo. Un mensaje nuevo que no cabe se rechaza antes de guardarse, sin truncarlo silenciosamente. El panel informa presupuesto, mensajes omitidos y memoria parcial.

Las solicitudes y sus respuestas parciales se guardan en SQLite, como máximo una vez por segundo durante streaming. Si el servidor reinicia, las que estaban ejecutándose pasan a interrumpidas y se conserva el texto guardado. Recargar una conversación recupera el seguimiento de una solicitud todavía activa. No se reenvía automáticamente el prompt, evitando generaciones duplicadas.

Cancelar cambia el estado del panel de inmediato y solicita cerrar la conexión HTTP. No equivale a apagar Kaggle ni prueba que el cálculo remoto terminó instantáneamente. Puede haber una espera hasta que una conexión en preparación responda. Máximo dos solicitudes del chat activas simultáneamente; los clientes externos mantienen su configuración propia.

## Almacenamiento recuperable

Ajustes del chat incluye cuota total (512 MB inicial, ajustable64–4096MB), reserva de espacio libre y plazo de archivo de pendientes (30 días inicial). Se contabilizan archivos originales y SQLite/journals, y se reserva espacio para respuestas en curso. Subidas y nuevos mensajes se rechazan si no hay presupuesto suficiente; no se borran conversaciones para hacer espacio.

Archivar pendientes antiguos afecta solamente adjuntos nunca enviados. Tanto ellos como conversaciones archivadas pueden restaurarse desde el panel. Los adjuntos restaurados reaparecen disponibles para enviar. Archivar no libera disco ni ejecuta purgas: un borrado definitivo requiere una política futura explícita.

## Video y visión

FFmpeg/FFprobe oficiales están instalados en la VPS. Un video de hasta180s/15MB se procesa por CPU, con timeout y como máximo cuatro JPEG de896px. La extracción real se probó con un video sintético de4s320×240, sin usar GPU. Se incluyen muestras visuales, no todo el video.

Los próximos notebooks preparan un auxiliar de visión abliterated de3,2GB: huihui_ai/qwen2.5-vl-abliterated:3b-instruct-q4_K_M, manifiesto fijado SHA25667f505b225fb4e9186e89a349659fd935520f7771b44fadbae340d7860c3987c. Fuente: https://ollama.com/huihui_ai/qwen2.5-vl-abliterated/tags y manifiesto público del registro Ollama. Solo se descarga cuando se pide el primer análisis visual en una sesión encendida. El gateway privado serializa inferencias y descarga de VRAM el coder antes de cargar visión; después descarga visión de VRAM y el coder vuelve a cargarse al responder. Esto añade latencia, pero evita mantener ambos residentes a la vez. No se descartan imágenes en silencio si falla visión. El código y el orden se probaron con servidor simulado; no se encendió GPU para verificar ese modelo aquí.

La transcripción de audio quedó instalada y activa por CPU: faster-whisper1.2.1, CTranslate2 4.8.5 y Whisper tiny multilingüe oficial (Systran/faster-whisper-tiny, revisión d90ca5fe260221311c53c58e660288d3deb8d356). Los75,5MBde pesos y archivos auxiliares se descargaron una sola vez y verificaron con SHA256 y objetos Git de la revisión fija. El modelo está en privado y configurado en IA_ASR_MODEL_DIR mediante drop-in systemd, conservando HOME, modo VPS y origen HTTPS. Usa CPUint8, dos hilos y90sde timeout; no descarga modelos durante consultas. Se convierte primero el audio con FFmpeg a PCMmono16kHz para evitar incompatibilidades de decodificación entre PyAVy faster-whisper. Una prueba real con voz sintética de FFmpegflite fue transcrita correctamente, incluyendo la palabra test; no fue una respuesta simulada. El audio embebido en videos no se transcribe automáticamente: el video usa fotogramas, y los archivos de audio se transcriben al adjuntarlos.

## Caché CPU real y diagnóstico

La preparación CPU privada de los pesos actuales de cuenta2 terminó COMPLETE. Se validó el manifiesto de revisión, nombre, tamaño16.998.720.992bytes y SHA256, y se adjuntó por una acción autenticada del panel. Los pesos permanecen en outputs privados de Kaggle y se montan con kernel_sources; no se descargaron17GB a la PC o VPS. Es una caché de outputs, no un dataset separado.

El próximo arranque de cuenta2 utilizará esa entrada y comprobará nuevamente SHA256 de los bytes montados. Ante falta/corrupción falla explícitamente en lugar de descargar otra copia en silencio. No se realizó un arranque GPU para medir ahorro ni confirmar el montaje en ejecución. El panel permite prepararCPU, consultar, verificar/adjuntar y desactivar; solo se adjunta con GPU parada y caché completa/verificada.

El nuevo gateway informa GPU/memoria/controlador, Python, CUDA declarada por entorno, versión de Ollama, origen de pesos y tiempos de carga. Esta información se recibe desde el próximo notebook, no se fabrica con datos de la PC. Flash attention y KV son opciones solicitadas, no prueba de aceleración medida.

## Verificación y estado final

88 pruebas en Linux pasan, incluyendo extracción real de fotogramas y transcripción real por CPU. En Windows se omiten las pruebas reales que requieren FFmpeg y el modelo ASR local, verificadas en la VPS. Sintaxis JavaScript válida y nuevos notebooks privados compilados. HTTPS autenticado200 para página, assets, historial, catálogo y almacenamiento; sin sesión401. Revisión independiente corrigió admisión de cuota también para mensajes y restauración de pendientes en UI. Respaldo de fuentes previo a deploy en almacenamiento privado.

Ambas GPU permanecen COMPLETE, sin listeners de inferencia18134/17860. La preparación CPU finalizó. La web sigue activa. No se hicieron benchmarks ni una nueva generación GPU. La herramienta de navegador no estuvo disponible en la revisión anterior; los controles se verificaron estáticamente y por HTTP, sin atribuir una comprobación visual de escritorio/móvil.


### Reproducir preparación de audio en otra VPS

Instalar `sistema/requirements-asr.txt` en el entorno Python3.12 del panel y ejecutar `python sistema/prepare_asr.py` como usuario del servicio. El script fija repositorio/revisión, tamaño y hashes y guarda los pesos bajo `.private/asr-models`. Copiar `deployment/asr-cpu.conf` a un drop-in de systemd después de verificar el modelo, recargar systemd y reiniciar solo el panel. La ruta del ejemplo asume `/opt/kaggle-ia`; ajustarla si la instalación usa otra ubicación. La presencia de un directorio vacío no habilita ASR. `tests_asr.py` comprueba configuración y voz real cuando el entorno está disponible.


## Verificación real posterior con autorización del usuario

Se inició únicamente la cuenta 2 y se deja encendida para su uso; la cuenta 1 permanece apagada. El arranque con caché verificada terminó LISTO y el modelo reportó contexto 131072 y unos 22 GB de VRAM. Paseo respondió PASEO_LISTO y su selector nativo muestra la cuenta 2 configurada.

La imagen de prueba fue interpretada correctamente como cuadrado rojo y círculo azul. La primera prueba de video confundió el orden de los colores: se corrigió el pipeline para describir cada fotograma individualmente, conservar índices y reutilizar observaciones de fotogramas idénticos dentro del mismo envío. La prueba final devolvió rojo/rojo/azul/azul en 0/1/2/3 segundos, contrastado con los píxeles reales del archivo. Esto valida el flujo de muestras, no garantiza interpretar todos los eventos de videos arbitrarios. El audio embebido no se transcribe automáticamente.

Se corrigió el caso de respuestas sin texto visible por agotar el presupuesto durante razonamiento: ahora se informa el error en lugar de mostrar una respuesta vacía como completada. Para este modelo con razonamiento medio se conservan los límites de salida habituales de 4096; una prueba limitada artificialmente a512 agotó su salida antes de contestar.

El navegador volvió a estar disponible: navegación de siete vistas, controles de almacenamiento/caché y chat móvil 390 px comprobados; se corrigió un aviso demasiado estrecho al compartir fila con varios botones. ASR figura como modelo local disponible. Las capturas privadas no se exportan.

Cierre: 91 pruebas pasan en Linux con ASR real habilitado; Windows91 con dos omitidas por no tener FFmpeg/modelo ASR local. Se ajustó además el panel móvil de historial, cuyo máximo de260px podía ocultar la lista bajo sus controles; seleccionar conversaciones volvió a comprobarse en el navegador.
