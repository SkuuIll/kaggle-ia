# Primer despliegue y configuración privada

El proyecto proviene de una instalación administrada. El instalador configura servicios y dependencias, pero no crea tu cuenta Kaggle, DNS, firewall ni usuario SSH de relay. No copies secretos de otra instalación. No ejecutes scripts como root sin revisarlos.

## Preparación

- Cloná el proyecto en `/opt/kaggle-ia` de una VPS Linux x86_64. Prepará `curl`, `tar`, `sha256sum`, OpenSSH y systemd.
- Copiá `sistema/model_profiles.example.json` a `sistema/model_profiles.json`. Reemplazá `CONFIGURAR_USUARIO` en los kernels por tu usuario Kaggle y revisá modelo, licencia, contexto y puertos. No habilites un segundo perfil sin una cuenta autorizada para él.
- Generá el acceso del panel con `python3 sistema/panel_password.py`. Solicita contraseña por entrada oculta y solo guarda el hash.
- Conservá toda configuración sensible en `sistema/.private/` (directorio0700, archivos0600). Agregá tus credenciales Kaggle desde la interfaz autenticada o como `sistema/kaggle(1).json` según el formato de la API. No incluyas ejemplos con tokens reales.

## Relay SSH (administrador)

Creá una clave SSH exclusiva y un usuario de relay sin shell. La clave debe permitir únicamente reverse forwarding sobre los puertos internos del perfil:18134 o17860 en127.0.0.1. Restringí `authorized_keys` con `restrict,port-forwarding,permitlisten="127.0.0.1:18134",permitlisten="127.0.0.1:17860"` y configurá sshd con `AllowTcpForwarding remote`, `GatewayPorts no`, sin TTY ni sesiones para ese usuario. Revisá con `sshd -t` antes de recargar, preservando tu acceso administrativo.

Guardá la clave privada exclusiva como `sistema/.private/kaggle_relay`, y la clave pública del host VPS verificada por un canal confiable en `sistema/.private/known_hosts`. No desactives StrictHostKeyChecking. La configuración `sistema/.private/connection.json` tiene esta forma (valores de ejemplo):

```json
{"host":"relay.example.com","user":"kaggle-relay","port":22,"panel_url":"https://ia.example.com"}
```

Los notebooks generados incorporan la clave de relay; mantenelos privados también en Kaggle. No los subas a este repositorio ni compartas sus salidas sensibles.

## Dominio y servicios

Reemplazá `ia.example.com` en `deployment/Caddyfile` y `IA_PUBLIC_ORIGIN` de `deployment/kaggle-ia.service` por tu dominio. Configurá DNS, acceso HTTPS y firewall. Seguí [VPS.md](VPS.md) para el instalador. Sus versiones y hashes están fijados; si una descarga deja de existir, revisá la versión y el hash oficial antes de actualizarlos.

Las claves de inferencia son distintas de las de Kaggle. Se administran privadamente; `api-clients.json` contiene los tokens de clientes y `inference-auth.json` sus SHA-256 por número de cuenta. No publiques ninguno de los dos. Consultá el código de `inference_auth.py` y el flujo de conexión del panel para el formato. Esta preparación inicial del relay y credenciales no es un asistente automático de un clic.

## Comprobaciones antes de usar

Probá el login, que la API rechace peticiones sin clave, los puertos internos enlazados solo a127.0.0.1 y la conexión SSH del notebook. Iniciá un perfil y comprobá una respuesta real; al apagar, verificá procesos y estado terminal oficial de Kaggle. Detené la sesión desde Kaggle si el canal de control no está disponible. Reiniciar el panel corta las conexiones HTTP en curso: evitá hacerlo durante generación.

El chat guarda conversaciones y adjuntos en la VPS. Respaldalos privadamente. FFmpeg y ASR son opcionales: consultá `requirements-asr.txt`, `prepare_asr.py` y `deployment/asr-cpu.conf`. Una prueba omitida por falta de dependencias no confirma soporte multimedia.
