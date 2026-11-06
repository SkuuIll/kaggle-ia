# ThinkingCap en dos Tesla T4

En **Plantillas**, elegí una cuenta y aplicá **ThinkingCap Nemotron 3.5 Lightning**. El panel verifica la revisión y el archivo, prepara un notebook privado y conserva el alias y la URL de los clientes. Después iniciá la cuenta desde **Cuentas**.

El perfil usa llama.cpp b12170 con CUDA, dos GPU, Flash Attention, KV Q8_0 y un único turno de inferencia a la vez. Reserva una ventana de 262.144 tokens y reutiliza el prefijo cuando es posible. En el benchmark recuperó cinco datos con 249.998 tokens de entrada. La velocidad medida fue de 78,9 TPS en código corto y 16,3 TPS en la consulta de recuperación a 249.998 tokens. Las pruebas largas posteriores reutilizaron parte del prefijo.

El modo **Directo** es el predeterminado. **Breve**, **Medio** y **Profundo** asignan presupuestos crecientes al razonamiento y dejan espacio para la respuesta final. La ventana incluye entrada y salida. El chat reserva tokens para responder y puede resumir u omitir historial antiguo del envío según su estimación, conservando el historial completo en la VPS.

Para volver al modelo anterior, aplicá **Qwen3.8 Heretic ARA · EXL3 + DFlash2**. Para usar Ollama y el análisis visual auxiliar, aplicá **Qwen3.8 RVN Heretic · Multilingual MTP**. El cambio de plantilla conserva las conversaciones.
