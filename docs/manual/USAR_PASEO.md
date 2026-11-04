# Usar Paseo con tu instalación

1. Iniciá una GPU desde tu panel y esperá a que la API responda. Una cola no equivale a un modelo listo.
2. En Configuración → Conexión elegí una cuenta y descargá el paquete privado de clientes.
3. Extraelo y seguí su guía para instalar/configurar Paseo y OpenCode en Windows. Revisá los cambios antes de aplicarlos a una configuración existente.
4. Iniciá el daemon de Paseo (`paseo daemon start`), abrí un chat nuevo y elegí el proveedor y modelo exportados.

La API usa `https://ia.example.com/inference/cuentaN/v1` con tu dominio y una clave dedicada. El broker de Paseo es local y es una conexión distinta. Nunca publiques paquetes de clientes: contienen una clave de inferencia. No se incluyen credenciales ni configuraciones aplicadas a otra PC en este repositorio.
