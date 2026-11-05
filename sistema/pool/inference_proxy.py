"""Loopback inference proxy. Persist only counts, never request/response content."""
import json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import requests
from urllib3.exceptions import HTTPError
from usage import UsageParser
from panel_security import local_host
INFERENCE={'/v1/chat/completions','/v1/completions','/v1/responses','/api/chat','/api/generate'}
def create_proxy(account,port,backend_port,store,auth_path=None):
    class Proxy(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.0'
        def log_message(self,*args):pass
        def do_GET(self):self.forward()
        def do_POST(self):self.forward()
        def forward(self):
            if not local_host(self.headers.get('Host',''),port):self.send_error(403);return
            path=self.path.split('?')[0]
            if self.headers.get('X-IA-Public')=='1':
                from inference_auth import allowed
                if auth_path is None or not allowed(self.headers.get('Authorization',''),account,auth_path):self.send_error(401,'API key required');return
                permitted=(self.command=='GET' and path=='/v1/models') or (self.command=='POST' and path in {'/v1/chat/completions','/v1/completions','/v1/responses'})
                if not permitted:self.send_error(404);return
            if not (path.startswith('/v1/') or path in {'/api/chat','/api/generate','/api/ps','/api/tags','/api/version'}):self.send_error(404);return
            try:length=int(self.headers.get('Content-Length','0'))
            except ValueError:self.send_error(400);return
            if length<0 or length>32*1024*1024:self.send_error(413);return
            data=self.rfile.read(length) if length else None
            model='';inference=self.command=='POST' and path in INFERENCE
            identity=store.identity(account) if inference else None
            if self.command=='POST':
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send_error(415);return
                try:
                    body=json.loads(data or b'{}');model=str(body.get('model',''))
                    if inference and body.get('stream') and path.startswith('/v1/'):
                        body['stream_options']={**body.get('stream_options',{}),'include_usage':True}
                        data=json.dumps(body).encode()
                except (ValueError,TypeError,AttributeError):self.send_error(400);return
            parser=UsageParser();started=time.monotonic();status=502;headers_sent=False
            try:
                with requests.request(self.command,f'http://127.0.0.1:{backend_port}'+self.path,data=data,headers={'Content-Type':'application/json'},stream=True,timeout=(10,600)) as response:
                    status=response.status_code;self.send_response(status);self.send_header('Content-Type',response.headers.get('Content-Type','application/json'));self.send_header('Cache-Control','no-store');self.end_headers();headers_sent=True
                    while True:
                        chunk=response.raw.read1(4096)
                        if not chunk:break
                        if inference:parser.feed(chunk)
                        self.wfile.write(chunk);self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError):status=499
            except (requests.RequestException,HTTPError):
                status=503
                if not headers_sent:
                    self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers()
                    self.wfile.write(json.dumps({'error':{'message':'El modelo esta apagado o todavia esta cargando. Revisa su estado en https://ia.example.com/#actividad.','type':'backend_unavailable'}}).encode())
            finally:
                if inference:
                    counts=parser.finish()
                    store.record(account,model,counts[0] if counts else None,counts[1] if counts else None,status,time.monotonic()-started,identity=identity)
    return ThreadingHTTPServer(('127.0.0.1',port),Proxy)
