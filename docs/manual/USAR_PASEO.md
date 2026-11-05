# Usar la IA de la cuenta 2 en Paseo

Configuración aplicada en esta PC: Paseo, OpenCode y Continue usan HTTPS y la clave dedicada de la cuenta 2. Las claves se conservan en los archivos privados de configuración, no en este manual.

1. Abrí Paseo (ya quedó abierto durante la configuración).
2. Creá un chat nuevo y elegí **Qwen3.8 RVN Heretic Kaggle (cuenta 2)**, o el proveedor **IA Kaggle** con el modelo **Cuenta 2: Qwen3.8 27B RVN Heretic**. La cuenta 2 está primera y marcada como predeterminada en los proveedores gestionados.
3. Elegí la carpeta de tu proyecto y escribí la tarea.

El identificador técnico conserva `kaggle2/qwen38-coder390` para mantener compatibilidad aunque el nombre visible del modelo haya cambiado. La dirección es `https://ia.example.com/inference/cuenta2/v1`; no usar localhost como API de la IA. El broker local de Paseo es otra conexión distinta y puede usar un puerto local normalmente.

La disponibilidad se confirma en el panel, no solo por que Paseo esté abierto: esperá LISTO tras arrancar. No hace falta volver a pegar el token Kaggle ni la clave de inferencia. Si un chat viejo mantiene una configuración anterior, abrí uno nuevo.

Cuando termines de trabajar, apagá la cuenta desde el panel y esperá confirmación de Kaggle. Cerrar Paseo no apaga la GPU. El autoapagado configurado de la cuenta también puede detenerla si no tiene solicitudes durante su plazo de inactividad; el panel informa sus límites.

Diagnóstico: Configuración > Conexión > Diagnosticar. Si la API está apagada o cargando, primero resolvé su estado desde el panel. Evitá repetir varias solicitudes mientras el modelo carga, ya que pueden quedar esperando. Las pruebas visuales pueden descargar/cargar un modelo auxiliar y demorar una respuesta que llegue al mismo tiempo.

## Comprobación real del cliente

El 2026-11-04 se corrigió el servicio local de Paseo detenido, se inició y se ejecutó una prueba con el proveedor qwen-coder390 y modelo kaggle2/qwen38-coder390. La respuesta fue PASEO_LISTO, sin leer ni modificar archivos del proyecto. El modelo sigue usando HTTPS. La prueba corresponde a la conversación 529c5b6c-7196-4e8e-bbe5-13339e0252f1 y workspace local kaggle.
