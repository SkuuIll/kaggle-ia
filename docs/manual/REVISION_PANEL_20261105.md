# Revisión del panel y del flujo de trabajo

## Comprobaciones por apartado

| Apartado | Qué se revisó | Resultado |
| --- | --- | --- |
| Dashboard | Estado, cuotas, gráficas, flujo rápido y conexión pool | Se reemplazó la promesa de rotación 24/7 por el estado del relay detectado. El pool enruta hacia una cuenta que ya responde. |
| Chat IA | Historial, borrador, adjuntos, contexto y estado de generación | El borrador se mantiene por conversación durante la visita. Los adjuntos en curso se guardan en su conversación original. Las respuestas fallidas quedan visibles y se excluyen del contexto enviado al modelo. |
| Cuentas | Estado autenticado, credenciales y control de ciclo de vida | Cuentas 1 y 2 en estado terminal COMPLETE. La suite cubre altas, reemplazos, bajas y protección de operaciones concurrentes. |
| Modelos y TPS | Carga de vista, selección, presupuestos y medición | La suite cubre presupuestos, repositorios fijados y recuento de uso. Queda pendiente medir rendimiento de una sesión nueva. |
| Plantillas | Catálogo HTTPS, validación de revisión y preparación | El catálogo responde con sesión. La suite valida el notebook generado y la preparación sin arrancar GPU. |
| Actividad | Navegación, historial y registro de operaciones | La vista abre en navegador y las pruebas cubren persistencia y prioridad de apagado. |
| Configuración | Sesión, almacenamiento, exportación y configuración de clientes | Se comprobó el acceso autenticado al almacenamiento. La exportación por CLI vuelve a resolver la raíz. Las pruebas de clientes comprueban URL HTTPS y credenciales por cuenta. |
| Móvil | Navegación por las siete vistas a 320, 390, 768 y 1280 px en Edge | Las vistas abren sin desplazamiento horizontal de página. Se comprobó la apertura y el cierre del historial táctil, el borrador y el botón Iniciar servidor. |
| VPS | Instalación de fuentes, Caddy, servicios y assets | Caddy validó la configuración. Los servicios quedaron activos y el módulo del chat se sirve desde su nueva ruta. |

El navegador interceptó la solicitud de inicio y confirmó la cuenta seleccionada. La prueba de interfaz usó conversaciones de ejemplo. El arranque real en Kaggle, la generación GPU y el ciclo de apagado y reinicio de una nueva sesión quedan por comprobar cuando se pulse **Iniciar servidor**.

Para operar el panel, consultá la [guía de chat y arranque](CHAT_Y_ARRANQUE.md). El [README](../../README.md) incluye el mapa del proyecto y los comandos de prueba.
