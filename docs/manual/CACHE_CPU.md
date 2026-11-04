# Caché privada de pesos con CPU

La preparación usa un notebook privado sin GPU ni TPU. Descarga un único GGUF desde Hugging Face en la revisión fijada y comprueba tamaño y SHA256 contra los metadatos LFS. No incrusta credenciales Kaggle, claves de inferencia ni SSH. Los pesos se descargan en Kaggle, no en la PC ni en la VPS.

Se aprovechan las salidas persistentes del notebook CPU como `kernel_sources` del notebook GPU. No se crea un dataset adicional ni se suben los pesos desde la VPS. Este es un mecanismo de caché privada montable, distinto de un directorio temporal que desaparece al terminar la sesión.

## Flujo desde el panel

1. Preparar valida el archivo y construye el programa CPU, todavía sin ejecutarlo.
2. Iniciar preparación publica y ejecuta únicamente ese notebook CPU. Si la misma revisión está en cola, ejecutándose o completa, se reutiliza el estado y no se duplica el trabajo.
3. Consultar estado espera COMPLETE y descarga solamente `manifest.json`; no descarga el GGUF a la VPS.
4. Adjuntar al próximo arranque exige manifiesto fresco que coincida exactamente con el modelo, revisión, tamaño y hash. El perfil guarda `cache_source`.
5. El siguiente notebook GPU monta esa salida y vuelve a calcular el SHA256 antes de importar los pesos en Ollama. No se envía una consulta de generación para comprobar la caché.

Cambiar de modelo o revisión desactiva una caché obsoleta en el constructor. Una caché configurada que no esté montada o falle su integridad produce un error explícito; no inicia una descarga externa silenciosa durante esa sesión GPU. La caché de una cuenta no puede usarse como salida privada de la otra cuenta.

## Límites y estado honesto

El máximo admitido es 18GiB por archivo, dejando margen en las salidas del notebook. Los modelos mayores se rechazan con una explicación. Los nuevos envíos establecen un límite de ejecución CPU de 1800 segundos. Preparación, COMPLETE, manifiesto verificado y uso real durante un arranque GPU son estados diferentes: que el manifiesto exista no demuestra todavía un arranque acelerado ni un ahorro de tiempo medido.

No se cambian cuotas ni se eluden políticas de Kaggle. La sesión CPU termina al finalizar el script. Las sesiones GPU permanecen apagadas hasta que el usuario elija iniciarlas. Los pesos y la salida siguen siendo privados; no publicar notebooks generados de inferencia que contienen la clave SSH.

## Diagnóstico del próximo runtime GPU

`/control/status` incluye un objeto `runtime` con Python, GPU/memoria/driver informados por nvidia-smi, CUDA_VERSION cuando el entorno lo proporciona, versión de Ollama y origen de los pesos. Flash Attention y tipo de KV cache se etiquetan como opciones solicitadas, sin afirmar una aceleración medida. Los tiempos de motor y de modelo listo se registran por separado. Consultar este diagnóstico no genera texto ni renueva el contador de inactividad.

## Pruebas

Las pruebas locales comprueban CPU-only/privacidad, revisión y archivo, rechazo de tamaños y hashes inválidos, no duplicar trabajos completos, manifiesto fresco, hash de contenido antes de leer caché y rechazo de otra cuenta. Los constructores de ambos notebooks privados compilan sin publicarlos ni iniciar GPU.
