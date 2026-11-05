"""Unified pool inference proxy. Routes transparently to any ready backend without changing client URLs."""
import json,socket,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import requests
from urllib3.exceptions import HTTPError
from usage import UsageParser
from panel_security import local_host

INFERENCE={'/v1/chat/completions','/v1/completions','/v1/responses','/api/chat','/api/generate'}

def is_backend_listening(port, timeout=0.3):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=timeout):
            return True
    except OSError:
        return False

def check_backend_ready(backend_port, timeout=0.8):
    if not is_backend_listening(backend_port, timeout=0.3):
        return False
    try:
        r = requests.get(f'http://127.0.0.1:{backend_port}/control/status', timeout=timeout)
        if r.status_code == 200:
            return True
    except (requests.RequestException, OSError):
        pass
    try:
        r = requests.get(f'http://127.0.0.1:{backend_port}/v1/models', timeout=timeout)
        return r.status_code == 200
    except (requests.RequestException, OSError):
        return False

def resolve_pool_backend(catalog_data, active_key=None, probe_fn=check_backend_ready):
    profiles = catalog_data.get('profiles', {})
    # Priority 1: Check currently selected / active profile
    if active_key and active_key in profiles:
        p = profiles[active_key]
        if p.get('enabled', True) and probe_fn(p.get('port', 18134)):
            return active_key, p
    # Priority 2: Check any enabled profile that is currently responding
    for key, p in profiles.items():
        if key != active_key and p.get('enabled', True):
            if probe_fn(p.get('port', 18134)):
                return key, p
    return None, None

def create_pool_proxy(port, store, auth_path=None, catalog_fn=None, wait_timeout=25):
    if catalog_fn is None:
        from model_profiles import catalog as catalog_fn

    class PoolProxy(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'
        def log_message(self, *args): pass
        def do_GET(self): self.forward()
        def do_POST(self): self.forward()
        def forward(self):
            if not local_host(self.headers.get('Host', ''), port):
                self.send_error(403)
                return
            path = self.path.split('?')[0]

            # Pool status endpoint
            if self.command == 'GET' and path == '/api/pool/status':
                data = catalog_fn()
                active_key, active_profile = resolve_pool_backend(data, data.get('selected'))
                resp = {
                    'pool_port': port,
                    'active_key': active_key,
                    'active_account': active_profile.get('account') if active_profile else None,
                    'active_model': active_profile.get('model') if active_profile else None,
                    'ready': active_key is not None
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode('utf-8'))
                return

            # Public auth verification: accept any valid configured key in the installation
            caller_account = 2
            if self.headers.get('X-IA-Public') == '1':
                auth_header = self.headers.get('Authorization', '')
                if not auth_header.startswith('Bearer ') or len(auth_header) > 512:
                    self.send_error(401, 'API key required')
                    return
                from inference_auth import allowed
                authenticated = False
                if auth_path is not None and Path(auth_path).exists():
                    try:
                        hashes = json.loads(Path(auth_path).read_text(encoding='utf8'))
                        for acc_id in hashes:
                            if allowed(auth_header, acc_id, auth_path):
                                authenticated = True
                                caller_account = int(acc_id) if str(acc_id).isdigit() else 2
                                break
                    except Exception:
                        pass
                if not authenticated:
                    self.send_error(401, 'API key required')
                    return
                permitted = (self.command == 'GET' and path == '/v1/models') or (self.command == 'POST' and path in {'/v1/chat/completions', '/v1/completions', '/v1/responses'})
                if not permitted:
                    self.send_error(404)
                    return

            if not (path.startswith('/v1/') or path in {'/api/chat', '/api/generate', '/api/ps', '/api/tags', '/api/version'}):
                self.send_error(404)
                return

            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self.send_error(400)
                return
            if length < 0 or length > 32 * 1024 * 1024:
                self.send_error(413)
                return
            data = self.rfile.read(length) if length else None
            model = ''
            inference = self.command == 'POST' and path in INFERENCE

            # Body parsing
            if self.command == 'POST':
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    self.send_error(415)
                    return
                try:
                    body = json.loads(data or b'{}')
                    model = str(body.get('model', ''))
                    if inference and body.get('stream') and path.startswith('/v1/'):
                        body['stream_options'] = {**body.get('stream_options', {}), 'include_usage': True}
                        data = json.dumps(body).encode()
                except (ValueError, TypeError, AttributeError):
                    self.send_error(400)
                    return

            # Resolve active backend, waiting briefly if currently rotating/switching
            started_wait = time.monotonic()
            active_key, active_profile = None, None
            while time.monotonic() - started_wait < wait_timeout:
                catalog_data = catalog_fn()
                active_key, active_profile = resolve_pool_backend(catalog_data, catalog_data.get('selected'))
                if active_key is not None:
                    break
                time.sleep(1.0)

            if active_key is None or active_profile is None:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': {
                        'message': 'El pool de IA está apagado o todas las cuentas están cargando. Revisa su estado en https://ia.example.com/#actividad.',
                        'type': 'backend_unavailable'
                    }
                }).encode('utf-8'))
                return

            backend_port = active_profile.get('port', 18134)
            account_id = active_profile.get('account', caller_account)
            identity = store.identity(account_id) if (store and inference) else None
            parser = UsageParser()
            started_req = time.monotonic()
            status = 502
            headers_sent = False

            try:
                with requests.request(self.command, f'http://127.0.0.1:{backend_port}' + self.path,
                                     data=data, headers={'Content-Type': 'application/json'},
                                     stream=True, timeout=(10, 600)) as response:
                    status = response.status_code
                    self.send_response(status)
                    self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    headers_sent = True
                    while True:
                        chunk = response.raw.read1(4096)
                        if not chunk:
                            break
                        if inference:
                            parser.feed(chunk)
                        self.wfile.write(chunk)
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                status = 499
            except (requests.RequestException, HTTPError):
                status = 503
                if not headers_sent:
                    self.send_response(503)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'error': {
                            'message': 'El modelo está apagado o todavía está cargando. Revisa su estado en https://ia.example.com/#actividad.',
                            'type': 'backend_unavailable'
                        }
                    }).encode('utf-8'))
            finally:
                if inference and store:
                    counts = parser.finish()
                    store.record(account_id, model, counts[0] if counts else None, counts[1] if counts else None,
                                 status, time.monotonic() - started_req, identity=identity)

    return ThreadingHTTPServer(('127.0.0.1', port), PoolProxy)
