# Arquitectura y Seguridad

## Flujo de conexión e inferencia

El sistema está diseñado para alojar el panel de control y el relay de inferencia en una VPS Linux, exponiendo únicamente rutas HTTPS autenticadas hacia los clientes autorizados:

- **Endpoint Cuenta 1:** `https://ia.example.com/inference/cuenta1/v1`
- **Endpoint Cuenta 2:** `https://ia.example.com/inference/cuenta2/v1`

Cada cuenta dispone de una **clave API Bearer dedicada**, independiente de la contraseña de acceso al panel web y de los tokens de Kaggle. El servidor almacena únicamente el hash SHA-256 de cada clave en `sistema/.private/inference-auth.json` para validar las peticiones entrantes en tiempo constante (`hmac.compare_digest`).

En las rutas públicas de inferencia (`/inference/cuentaN/*`), Caddy inyecta la cabecera `X-IA-Public: 1` y el proxy permite exclusivamente endpoints compatibles con OpenAI:
- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/completions`
- `POST /v1/responses`

Cualquier intento de invocar rutas administrativas de Ollama (`/api/pull`, `/api/create`, `/api/delete`, etc.) o de acceder sin el token Bearer correspondiente a esa cuenta es rechazado con `401` o `404`.

---

## Topología de puertos internos en la VPS

Todos los servicios internos escuchan exclusivamente en la interfaz de loopback (`127.0.0.1`):

| Componente | Dirección local | Función |
|---|---|---|
| Túnel inverso Cuenta 1 | `127.0.0.1:18134` | Gateway privado dentro del notebook de Kaggle (Cuenta 1) |
| Túnel inverso Cuenta 2 | `127.0.0.1:17860` | Gateway privado dentro del notebook de Kaggle (Cuenta 2) |
| Proxy medido Cuenta 1 | `127.0.0.1:19134` | Valida Bearer, inyecta `include_usage` en streaming y registra tokens |
| Proxy medido Cuenta 2 | `127.0.0.1:19860` | Valida Bearer, inyecta `include_usage` en streaming y registra tokens |
| Servidor del panel | `127.0.0.1:8765` | Interfaz web, API de gestión y recepción de etapas `/api/runtime` |
| Caddy Admin API | `127.0.0.1:2020` | Administración local de Caddy |
| Caddy HTTPS | `:80` / `:443` | Único punto de entrada público TLS con `flush_interval -1` |

La conexión desde el notebook de Kaggle hacia la VPS utiliza una clave SSH restringida (`sistema/.private/kaggle_relay`) con `StrictHostKeyChecking=yes` contra `sistema/.private/known_hosts`, sin acceso a shell interactivo y con permisos `permitopen` limitados a los puertos de loopback configurados.

---

## Autenticación del panel web y sesiones

1. **Almacenamiento de contraseñas:** la contraseña del administrador se guarda como hash `scrypt` (`n=16384, r=8, p=1`) con sal aleatoria de 16 bytes en `sistema/.private/panel-auth.json` y límite de intentos por IP.
2. **Cookie de sesión:** tras autenticar en `/login`, el servidor emite una cookie `__Host-ia_session` con atributos `HttpOnly`, `Secure`, `SameSite=Strict` y vigencia máxima de 8 horas en memoria.
3. **Protección CSRF y origen:** cada sesión recibe un token CSRF único. Todas las operaciones `POST` verifican el encabezado `Host`, el encabezado `Origin` contra `IA_PUBLIC_ORIGIN` y el token `X-IA-Token`. El frontend sincroniza automáticamente el token CSRF desde `/api/session` si una pestaña quedó abierta tras un reinicio.
4. **Revocación inmediata:** cerrar sesión invalida el token en el servidor; cambiar la contraseña desde el panel o reiniciar el servicio `kaggle-ia` revoca todas las sesiones activas sin interrumpir las GPUs en ejecución.

---

## Estado privado y persistencia en SQLite

Los archivos sensibles residen fuera del árbol público:
- `sistema/kaggle(1).json` y `sistema/kaggle(2).json`: credenciales de la API de Kaggle por cuenta.
- `sistema/model_profiles.json`: catálogo activo de modelos, contextos y referencias de notebooks.
- `sistema/.private/`: claves SSH (`kaggle_relay`, `known_hosts`), configuración del relay (`connection.json`), hashes de acceso (`panel-auth.json`, `inference-auth.json`), claves de clientes (`api-clients.json`) y base de datos `usage.sqlite`.

La base de datos `usage.sqlite` registra:
- **Tabla `requests`:** marca temporal, cuenta, identidad de usuario de Kaggle, nombre del modelo, tokens de entrada, tokens de salida, código HTTP y duración. **Nunca almacena prompts ni respuestas.**
- **Tabla `connections`:** vincula cada ranura de conexión con el nombre de usuario de Kaggle actual para aislar las métricas históricas si se reemplaza una cuenta.
- **Tabla `events`:** historial persistente de operaciones del panel (inicios, paradas, cambios de plantilla, exportaciones y motivos de autoapagado) con mensajes de diagnóstico sanitizados.
