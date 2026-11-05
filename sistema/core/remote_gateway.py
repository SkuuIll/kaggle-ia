def runtime_limits(started,idle,active,now,idle_minutes,maximum):
 return {'idle_remaining':max(0,int(idle_minutes*60-(now-idle))) if not active else None,'session_remaining':max(0,int(maximum*60-(now-started)))}


"""Gateway privado de inferencia y parada; accesible solo mediante SSH."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading, time, requests, json
stop_event = threading.Event()
last_activity = time.monotonic()
started_at = last_activity
active_requests = 0
session_started = started_at
session_extension = 0
idle_policy = 15
maximum_policy = 120
lock = threading.Lock()
inference_guard = threading.Lock()
class Gateway(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    def log_message(self, *args): pass
    def do_GET(self):
        if self.path == '/control/status':
            import shutil
            from pathlib import Path
            with lock:
                data={'uptime_seconds':int(time.monotonic()-started_at),'idle_seconds':int(time.monotonic()-last_activity),'active_requests':active_requests}
            data.update(capabilities=['session-v1','vision-v1'],**runtime_limits(session_started,last_activity,active_requests,time.monotonic(),idle_policy,maximum_policy+session_extension))
            data['runtime']=globals().get('runtime_fingerprint',{})
            data['disk']={p:dict(zip(('total','used','free'),shutil.disk_usage(p))) for p in ('/','/kaggle/temp','/kaggle/working') if Path(p).exists()}
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(json.dumps(data).encode());return
        self.proxy()
    def do_DELETE(self): self.proxy()
    def do_POST(self):
        if self.path == '/control/vision':
            global last_activity,active_requests
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=24*1024*1024:raise ValueError('Tamaño de entrada visual no permitido.')
                payload=json.loads(self.rfile.read(length))
                with lock:active_requests+=1;last_activity=time.monotonic()
                try:
                    with inference_guard:result=analyze_visual(config['model'],payload.get('images'),payload.get('prompt','Describí las imágenes y cualquier texto visible.'),requests)
                finally:
                    with lock:active_requests-=1;last_activity=time.monotonic()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(result).encode())
            except Exception as error:
                self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'error':'No se completó el análisis visual: '+type(error).__name__}).encode())
            return
        if self.path == '/control/extend':
            global session_extension
            with lock:
                if session_extension>=120:self.send_error(409);return
                session_extension=min(120,session_extension+30);last_activity=time.monotonic()
            self.send_response(200);self.end_headers();self.wfile.write(b'{"extended_minutes":30}');return
        if self.path == '/control/stop':
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"stop_requested"}'); self.wfile.flush(); stop_event.set(); return
        self.proxy()
    def proxy(self):
        global last_activity, active_requests
        if not self.path.startswith(('/v1/', '/api/')):
            self.send_error(404); return
        activity=self.command=='POST' and self.path.split('?')[0] in {'/api/chat','/api/generate','/api/embed','/api/embeddings','/v1/chat/completions','/v1/completions','/v1/embeddings','/v1/responses'}
        if activity:
            with lock:
                active_requests += 1; last_activity = time.monotonic()
            inference_guard.acquire()
        try:
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            if body and self.path.split('?')[0] == '/v1/chat/completions':
                try:
                    payload = json.loads(body)
                    eff = payload.get('reasoning_effort')
                    if eff is not None and eff not in ('low', 'medium', 'xhigh'):
                        payload['reasoning_effort'] = 'low' if eff == 'none' else 'xhigh' if eff == 'high' else 'medium'
                        body = json.dumps(payload).encode('utf-8')
                except Exception:
                    pass
            with requests.request(self.command, 'http://127.0.0.1:11434'+self.path, data=body or None, headers={'Content-Type':'application/json'}, stream=True, timeout=(10,600)) as res:
                self.send_response(res.status_code)
                self.send_header('Content-Type', res.headers.get('Content-Type','application/json')); self.end_headers()
                for chunk in res.iter_content(chunk_size=1):
                    self.wfile.write(chunk); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError): pass
        except Exception as exc:
            print('Gateway error:', type(exc).__name__, flush=True)
        finally:
            if activity:
                with lock:
                    active_requests -= 1; last_activity = time.monotonic()
                inference_guard.release()
server = ThreadingHTTPServer(('127.0.0.1', 18134), Gateway)
threading.Thread(target=server.serve_forever, daemon=True).start()
