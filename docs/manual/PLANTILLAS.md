# Catálogo de Plantillas, Modelos y Herramientas

La sección **Plantillas** del panel web permite explorar, buscar y filtrar un catálogo curado de modelos GGUF de baja restricción, empaquetadores de herramientas locales y flujos de trabajo (prompts) para desarrollo de software.

---

## 1. Modelos GGUF curados (variantes de baja restricción)

Todos los modelos del catálogo tienen su repositorio, nombre de archivo, tamaño exacto y hash de revisión (`SHA`) fijados y verificados en Hugging Face:

| ID | Modelo | Arquitectura en T4 ×2 | TPS estimados | Pesos | Contexto inicial |
|---|---|---|---|---:|---:|
| `qwen3-coder30` | **Qwen3 Coder 30B A3B · Abliterated** (`Q4_K_M`) | MoE 30B (3,3B activos/token) | **45–62 TPS** | 18,56 GB | `32.768` |
| `cybertiel` | **Cyber-Tiel 35B A3B · MTP** (`Q4_K_S`) | MoE 35B (3B activos + MTP ×4) | **42–60 TPS** | 21,28 GB | `131.072` |
| `qwen36-35b-mtp` | **Qwen3.6 35B A3B · MTP Abliterated** (`Q4_K`) | MoE 35B (3B activos + MTP ×4) | **45–65 TPS** | 21,71 GB | `32.768` |
| `qwen35-9b` | **Qwen3.5 9B · Abliterated** (`Q4_K_M`) | Denso 9B (1× T4 sin PCIe) | **48–64 TPS** | 5,63 GB | `32.768` |
| `coder14` | **Qwen2.5 Coder 14B · Abliterated** (`Q4_K_M`) | Denso 14B (1× T4 sin PCIe) | **28–36 TPS** | 8,99 GB | `32.768` |
| `coder7` | **Qwen2.5 Coder 7B · Abliterated** (`Q4_K_M`) | Denso 7B (1× T4 sin PCIe) | **55–72 TPS** | 4,68 GB | `16.384` |
| `qwen3-8b` | **Qwen3 8B · Abliterated** (`Q4_K_M`) | Denso 8B (1× T4 sin PCIe) | **52–68 TPS** | 5,03 GB | `16.384` |
| `coder390` | **Qwen3.8 Coder390 27B · Abliterated** (`Q4_K_M`) | Denso 27B (2× T4 completo) | **12–18 TPS** | 16,81 GB | `131.072` |

### Cómo funciona la instalación de una plantilla de modelo

1. Elegí la **Cuenta de destino** en la barra superior de **Plantillas** y pulsá **Instalar plantilla**.
2. El servidor verifica que la cuenta esté apagada en Kaggle (o solicita y confirma su parada si estaba activa).
3. Comprueba en línea contra la API de Hugging Face que la revisión SHA, el archivo GGUF y el tamaño en bytes coincidan exactamente con la receta fijada.
4. Actualiza el perfil conservando la cuenta, el alias del modelo, los puertos de relay y el slug del notebook privado, y regenera el notebook validando su sintaxis AST. Si algún paso falla, revierte automáticamente el catálogo al estado anterior.
5. **No inicia la GPU ni descarga pesos en este paso:** los pesos se descargan en Kaggle recién cuando pulsás **Encender**.
6. Tras cambiar de plantilla, abrí **Configuración → Conexión** para actualizar la configuración de tus clientes con el nuevo límite de contexto.

---

## 2. Paquetes de herramientas para tu PC

Desde **Plantillas → Herramientas y librerías**, podés generar un instalador privado en formato ZIP preconfigurado para la cuenta seleccionada:

| Herramienta | Paquetes fijados | Descripción |
|---|---|---|
| **Aider · asistente de terminal** | `aider-chat==0.86.2` | Agente de programación en terminal conectado a tu API HTTPS (`--no-auto-commits`, `--analytics-disable`). |
| **Cliente Python · HTTPX** | `httpx==0.28.1` | Script base en Python para consultar `/models` (sin gasto de GPU) o enviar prompts por CLI (`--prompt`). |
| **Chat web local · Streamlit** | `streamlit==1.66.1`, `httpx==0.28.1` | Interfaz de chat ligera en `http://127.0.0.1:8501` que envía los últimos 12 mensajes de la sesión. |

### Uso de los paquetes descargables

1. Pulsá **Preparar instalador privado** en la tarjeta de la herramienta y descargá el archivo ZIP.
2. Extraelo en una carpeta fuera de tus repositorios públicos y ejecutá `INSTALAR.bat` (requiere Python 3.12; crea un entorno `.venv` aislado).
3. Cuando tu modelo esté **LISTO** en el panel, ejecutá `ABRIR.bat` dentro de esa carpeta.

> **Seguridad:** Cada paquete contiene un archivo `connection.json` con la URL HTTPS y la clave Bearer de inferencia de la cuenta elegida (nunca contiene claves de Kaggle ni la clave SSH de la VPS). El archivo `.gitignore` interno del paquete bloquea todo (`*`) por seguridad.

---

## 3. Instrucciones de trabajo (Workflows)

El catálogo incluye cinco plantillas de prompts estructuradas listas para copiar con un clic y usar en Continue, Paseo o Aider:
- **Crear una interfaz web:** diseño accesible, responsive y manejo completo de estados (`loading`, `empty`, `error`).
- **Diagnosticar y corregir errores:** reproducción verificable, análisis de causa raíz y prueba de regresión.
- **Refactorizar con cambios controlados:** preservación de interfaces observables y verificación con tests existentes.
- **Generar pruebas útiles:** cobertura de requisitos, errores reales y casos límite sin acoplarse a detalles internos.
- **Documentar e instalar un proyecto:** guía reproducible de arquitectura, configuración segura, operación y solución de fallos.
