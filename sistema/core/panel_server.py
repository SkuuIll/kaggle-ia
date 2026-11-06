"""Local dashboard and measured inference routes. Never starts GPUs on page load."""
import json,os,re,secrets,subprocess,sys,threading,time,uuid
from collections import ChainMap
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import requests
from model_profiles import catalog,sync_clients,CATALOG
from model_settings import parse_repo,update_model
from usage import UsageStore
from inference_proxy import create_proxy
from inference_pool import create_pool_proxy
from panel_security import panel_host,mutation_allowed,login_return_target,file_login_redirect,attachment_headers
from chat_engine import ChatStore
BASE=Path(__file__).resolve().parent
if BASE.name in ('chat','pool','accounts','clients','core','templates','web','tests'):BASE=BASE.parent;ROOT=BASE.parent;PORT=8765
ACTIONS={'start','stop','stop_all','model','credentials','timers','accounts','paseo','add_account','remove_account','rename_account','export_program','export_private','restore','profile','extend','install_template','cache_prepare','cache_launch','cache_status','cache_attach','cache_detach'}

def save_catalog(data):
    target=CATALOG.with_suffix('.pending');target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');target.replace(CATALOG)

def inspect_model(repo):
    repo=parse_repo(repo);response=requests.get('https://huggingface.co/api/models/'+repo,timeout=30);response.raise_for_status();data=response.json()
    files=[x['rfilename'] for x in data.get('siblings',[]) if x['rfilename'].endswith('.gguf') and not any(s in x['rfilename'].lower() for s in ('mmproj','draft','imatrix')) and not re.search(r'-\d{5}-of-\d{5}',x['rfilename'])]
    files.sort(key=lambda x:('Q4_K_M' not in x,'Q4_K_S' not in x,x))
    if not files:raise ValueError('No hay un GGUF unico en este repositorio. Los modelos divididos no estan soportados por este asistente.')
    return {'repo':repo,'revision':data['sha'],'files':files,'native_context':data.get('gguf',{}).get('context_length')}

class Dashboard:
    def __init__(self):
        self.token=secrets.token_urlsafe(32);self.lock=threading.Lock();self.operation=threading.Lock()
        self.snapshots={};self.job={'status':'idle','lines':[]}
        self.runtime={};self.downloads={};self.refresh_trigger=threading.Event()
        self.cancel_file=BASE/'.private/panel-cancel';self.stop_pending=False
        self.store=UsageStore(BASE/'.private/usage.sqlite')
        self.chat=ChatStore(BASE)
    def refresh(self):
        for key,p in catalog()['profiles'].items():
            if not (BASE/f'kaggle({p["account"]}).json').exists():
                value={'state':'NOT_CONFIGURED','quota':None,'checked_at':time.time()}
            else:
                try:
                    result=subprocess.run([sys.executable,str(BASE/'coding_control.py'),'snapshot',key],capture_output=True,text=True,encoding='utf8',timeout=30)
                    if result.returncode:raise RuntimeError('No se pudo consultar Kaggle; revisa el token.')
                    value=json.loads(result.stdout.strip().splitlines()[-1])
                    if value['state']=='RUNNING':
                        url='http://127.0.0.1:'+str(p['port'])
                        try:
                            live=requests.get(url+'/control/status',timeout=2)
                            live.raise_for_status()
                            value['live']=live.json()
                            value['live']['model_ready']=False
                            resident=requests.get(url+'/api/ps',timeout=2)
                            resident.raise_for_status()
                            value['live']['model_ready']=any(
                                m.get('name','').split(':')[0]==p['model']
                                for m in resident.json().get('models',[]))
                        except (requests.RequestException,ValueError):pass
                except Exception as error:value={'state':'UNKNOWN','quota':None,'error':str(error)[:160],'checked_at':time.time()}
            with self.lock:self.snapshots[key]=value
    def monitor(self):
        while True:
            self.refresh();self.refresh_trigger.wait(30);self.refresh_trigger.clear()
    def state(self):
        with self.lock:snapshots=dict(self.snapshots);job={**self.job,'lines':list(self.job.get('lines',[]))}
        accounts=[]
        for key,p in catalog()['profiles'].items():
            try:username=json.loads((BASE/f'kaggle({p["account"]}).json').read_text())['username']
            except (OSError,ValueError,KeyError):username=None
            accounts.append({'key':key,'account':p['account'],'enabled':p.get('enabled',True),'configured':(BASE/f'kaggle({p["account"]}).json').exists(),
                'template_id':p.get('template_id'),'runtime':self.runtime.get(key),'performance_profile':p.get('performance_profile','contexto'),'username':username,'nickname':p.get('nickname',''),'model':p['model'],'revision':p['revision'],'daily':self.store.daily(p['account'],username),
                'label':p['label'],'repo':p['repo'],'filename':p['filename'],'context':p['context'],'idle_minutes':p.get('idle_minutes',15),
                'max_session_minutes':p.get('max_session_minutes',120),'client_url':(os.environ['IA_PUBLIC_ORIGIN']+'/inference/cuenta'+str(p['account'])+'/v1') if os.environ.get('IA_SERVER_MODE')=='vps' and os.environ.get('IA_PUBLIC_ORIGIN') else 'http://127.0.0.1:'+str(p.get('client_port',p['port']))+'/v1',
                'usage':self.store.totals(p['account'],username),**(snapshots.get(key,{'state':'CHECKING','quota':None}) if username else {'state':'NOT_CONFIGURED','quota':None})})
        return {'accounts':accounts,'job':job,'history':self.store.events(),'server_time':time.time(),'server_mode':os.environ.get('IA_SERVER_MODE','local'),'metrics_since':'Solo solicitudes que pasan por este panel; no se recuperan tokens anteriores.'}
    def log(self,line):
        if 'PRIVATE KEY' in line or 'KGAT_' in line:return
        with self.lock:
            self.job['lines'].append(line[:300]);self.job['lines']=self.job['lines'][-120:]
    def control(self,action,key):
        env={**os.environ,'PYTHONUTF8':'1','PYTHONUNBUFFERED':'1'}
        if action=='start':env['IA_CANCEL_FILE']=str(self.cancel_file)
        process=subprocess.Popen([sys.executable,str(BASE/'text_control.py'),action,key],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',cwd=BASE,env=env)
        published=threading.Event()
        def cancel_wait():
            while process.poll() is None:
                if action=='start' and published.is_set() and self.cancel_file.exists():
                    process.terminate();return
                time.sleep(.2)
        if action=='start':threading.Thread(target=cancel_wait,daemon=True).start()
        for line in process.stdout:
            line=line.strip()
            if line.startswith('['):published.set()
            if line.startswith(('[' ,'LISTO:','Configurado:','Comprobando','Parada solicitada','Kaggle confirma','No hay una')):self.log(line)
            elif line.startswith('ERROR:'):self.log('La operacion fallo; no se confirmo su resultado. Revisa la cuenta y Active Events de Kaggle.')
        if process.wait()!=0:raise RuntimeError('No se completo la operacion; no se anuncia inicio o parada confirmados.')
    def start(self,key,switch):
        from coding_control import probe_state
        if self.cancel_file.exists():raise ValueError('Inicio cancelado por solicitud de apagado.')
        for other in catalog()['profiles']:
            if other!=key and probe_state(other) in ('RUNNING','QUEUED'):
                if not switch:raise ValueError('Otra cuenta sigue activa. Confirma el cambio para apagarla primero.')
                self.control('stop',other)
        if self.cancel_file.exists():raise ValueError('Inicio cancelado por solicitud de apagado.')
        self.control('start',key)
    def begin(self,data):
        if not isinstance(data.get('action'),str) or data['action'] not in ACTIONS:raise ValueError('Accion no reconocida.')
        if data.get('key') is not None and (not isinstance(data['key'],str) or data['key'] not in catalog()['profiles']):raise ValueError('Cuenta invalida.')
        with self.lock:
            if self.stop_pending:raise ValueError('Hay un apagado pendiente; espera a que termine.')
            acquired=self.operation.acquire(blocking=False)
            if not acquired:
                if data.get('action') not in ('stop','stop_all'):raise ValueError('Ya hay una operacion en curso. Espera a que termine.')
                self.stop_pending=True;self.cancel_file.touch()
        if not acquired:
            self.log('Apagado solicitado durante la operacion; se cancela el inicio y luego se comprueba Kaggle.')
            def priority_stop():
                self.operation.acquire()
                with self.lock:self.stop_pending=False;self.job={'status':'running','action':data['action'],'lines':['Comprobando apagado solicitado...']}
                self.run(data)
            threading.Thread(target=priority_stop,daemon=True).start();return
        self.cancel_file.unlink(missing_ok=True)
        with self.lock:self.job={'id':uuid.uuid4().hex,'status':'running','action':data.get('action'),'started_at':time.time(),'lines':[]}
        threading.Thread(target=self.run,args=(data,),daemon=True).start()
    def run(self,data):
        detail=''
        try:
            action=data.get('action');key=data.get('key')
            if action not in {'stop_all','export_program','export_private','restore','accounts','paseo','add_account'} and key not in catalog()['profiles']:raise ValueError('Cuenta invalida.')
            if action=='add_account':self.credentials(None,data)
            elif action=='start':
                self.start(key,bool(data.get('switch')))
                if data.get('open_paseo') and os.environ.get('IA_SERVER_MODE')!='vps':
                    from ia_manager import open_paseo
                    open_paseo()
            elif action=='paseo':
                if os.environ.get('IA_SERVER_MODE')=='vps':raise ValueError('Paseo se abre en tu PC local.')
                from ia_manager import open_paseo
                open_paseo()
            elif action=='stop':self.control('stop',key)
            elif action=='stop_all':
                failed=False
                for other,p in catalog()['profiles'].items():
                    if not (BASE/f'kaggle({p["account"]}).json').exists():continue
                    try:self.control('stop',other)
                    except Exception:failed=True;self.log('No se confirmo la parada de cuenta '+str(p['account']))
                if failed:raise RuntimeError('Al menos una parada no esta confirmada. Revisa Active Events.')
                self.log('Las IA configuradas de este proyecto estan finalizadas en Kaggle.')
            elif action=='model':
                info=inspect_model(data.get('repo',''));context=int(data.get('context',131072));filename=data.get('filename','')
                if filename not in info['files'] or not 4096<=context<=1048576:raise ValueError('Archivo o contexto invalido.')
                if info['native_context'] and context>int(info['native_context']):raise ValueError('El contexto supera el nativo informado por el modelo.')
                self.control('stop',key)
                if self.cancel_file.exists():raise ValueError('Cambio de modelo cancelado por solicitud de apagado.')
                update_model(CATALOG,key,info['repo'],filename,info['revision'],context,True)
                self.log('Modelo guardado con revision fija. No se descargaron pesos en esta PC.')
                if data.get('start'):self.start(key,bool(data.get('switch')))
            elif action=='credentials':self.credentials(key,data)
            elif action=='rename_account':
                config=catalog();name=str(data.get('name','')).strip()
                if not 1<=len(name)<=48 or any(ord(c)<32 for c in name):raise ValueError('Usa un nombre de 1 a 48 caracteres.')
                config['profiles'][key]['nickname']=name;save_catalog(config);self.log('Nombre de cuenta actualizado.')
            elif action=='remove_account':
                from coding_control import probe_state
                from account_management import remove_account
                if data.get('stop'):self.control('stop',key)
                config=catalog();archive=remove_account(config,key,BASE,probe_state)
                try:save_catalog(config)
                except Exception:
                    archive.replace(BASE/f'kaggle({config["profiles"][key]["account"]}).json');raise
                self.log('Cuenta quitada del panel despues de confirmar su parada. Credencial archivada en privado para recuperacion.')
            elif action in ('cache_prepare','cache_launch','cache_status','cache_attach','cache_detach'):
                from cpu_cache import prepare,launch,status
                from coding_control import api,probe_state
                config=catalog();profile=config['profiles'][key]
                if action in ('cache_attach','cache_detach') and probe_state(key) not in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'):raise ValueError('Confirma la parada de la GPU antes de cambiar su caché.')
                if action=='cache_prepare':
                    info,_=prepare(profile,key,BASE);result={'state':'PREPARED','kernel_ref':info['kernel_ref']}
                elif action=='cache_detach':profile.pop('cache_source',None);save_catalog(config);result={'state':'DETACHED'}
                else:
                    client=api(profile)
                    result=launch(profile,key,BASE,client) if action=='cache_launch' else status(profile,key,BASE,client,attach=action=='cache_attach')
                    if action=='cache_attach':save_catalog(config)
                self.log('Caché CPU: '+str(result.get('state'))+'; adjunta='+str(bool(result.get('attached')))+'. Preparada no significa descargada; no se inició GPU.')
                with self.lock:self.job['cache']=result
            elif action=='install_template':self.install_template(key,data.get('template'),data.get('stop') is True)
            elif action=='profile':
                from operations import PROFILES,apply_profile
                preset=data.get('preset')
                if preset not in PROFILES:raise ValueError('Perfil invalido.')
                config=catalog();p=config['profiles'][key];preset_data=PROFILES[preset]
                apply_profile(p,preset)
                save_catalog(config);self.log('Perfil guardado para el proximo arranque. Descarga la configuracion actualizada para tus clientes.')
            elif action=='extend':
                p=catalog()['profiles'][key];url='http://127.0.0.1:'+str(p['port'])
                status=requests.get(url+'/control/status',timeout=5).json()
                if 'session-v1' not in status.get('capabilities',[]):raise ValueError('Este notebook anterior no admite extension. Disponible tras el proximo arranque.')
                requests.post(url+'/control/extend',timeout=5).raise_for_status();self.log('Sesion extendida 30 minutos; tambien se renovo la inactividad.')
            elif action=='timers':
                config=catalog();p=config['profiles'][key];idle=int(data['idle']);maximum=int(data['maximum'])
                if not 1<=idle<=120 or not 5<=maximum<=120:raise ValueError('Inactividad:1-120 minutos. Limite de sesion:5-120.')
                p.update(idle_minutes=idle,max_session_minutes=maximum);save_catalog(config)
                self.log('Autoapagado guardado para el proximo inicio. No cambia una sesion ya encendida.')
            elif action=='accounts':
                from coding_control import probe_state
                config=catalog();count=int(data.get('count',2))
                if count not in (1,2):raise ValueError('Selecciona una o dos cuentas.')
                if count==1 and probe_state('coder2') in ('RUNNING','QUEUED'):raise ValueError('Apaga la cuenta 2 antes de ocultarla.')
                config['profiles']['coder2']['enabled']=count==2
                if count==1:config['selected']='rapido'
                save_catalog(config);sync_clients(config['selected']);self.log('Numero de cuentas configurado.')
            elif action.startswith('export_'):
                from portability import export_program,export_private
                folder=ROOT/'exportaciones';stamp=time.strftime('%Y%m%d-%H%M%S')
                private=action=='export_private'
                result=(export_private if private else export_program)(ROOT,folder/(('conexion-PRIVADA-' if private else 'instalador-ia-')+stamp+'.zip'))
                download=uuid.uuid4().hex
                with self.lock:
                    self.downloads[download]=result
                    self.job['download']={'id':download,'filename':result.name,'private':private}
                self.log('Creado: '+str(result))
                if private:self.log('Este respaldo contiene tus claves. No lo publiques ni lo compartas.')
            elif action=='restore':
                import base64,tempfile
                from portability import import_private
                from coding_control import probe_state
                for existing,profile in catalog()['profiles'].items():
                    if (BASE/f'kaggle({profile["account"]}).json').exists() and probe_state(existing) not in ('COMPLETE','CANCEL_ACKNOWLEDGED','ERROR','MISSING'):
                        raise ValueError('Confirma el apagado de las cuentas actuales antes de importar otra conexion.')
                raw=base64.b64decode(data.get('zip',''),validate=True)
                if len(raw)>16*1024*1024:raise ValueError('Respaldo demasiado grande.')
                with tempfile.NamedTemporaryFile(suffix='.zip',delete=False) as temp:temp.write(raw);path=Path(temp.name)
                try:import_private(ROOT,path)
                finally:path.unlink(missing_ok=True)
                sync_clients(catalog()['selected']);self.log('Conexion privada importada. No se inicio ninguna GPU.')
            else:raise ValueError('Accion no reconocida.')
            with self.lock:self.job['status']='done';self.job['finished_at']=time.time()
        except Exception as error:
            self.log(str(error)[:240])
            from operations import failure_detail
            detail=failure_detail(error)
            with self.lock:self.job['status']='error'
        finally:
            try:self.store.event(data.get('action'),data.get('key'),self.job['status'],detail)
            except Exception:self.log('No se pudo guardar el historial de esta operacion.')
            self.operation.release();self.refresh()
    def install_template(self,key,identifier,stop=False):
        from coding_control import probe_state
        from templates import get_template,prepare_profile
        template=get_template(identifier)
        terminal=('COMPLETE','CANCEL_ACKNOWLEDGED','ERROR','MISSING')
        state=probe_state(key)
        if state not in terminal:
            if not stop:raise ValueError('Apaga la cuenta y confirma su parada antes de instalar esta plantilla.')
            self.control('stop',key)
            if probe_state(key) not in terminal:raise ValueError('No se confirmo el apagado. Plantilla sin cambios.')
        if self.cancel_file.exists():raise ValueError('Instalacion cancelada por solicitud de apagado.')
        response=requests.get('https://huggingface.co/api/models/'+template['repo']+'/revision/'+template['revision'],params={'blobs':'true'},timeout=30)
        response.raise_for_status()
        old=catalog();config=json.loads(json.dumps(old))
        config['profiles'][key]=prepare_profile(config['profiles'][key],identifier,response.json())
        save_catalog(config)
        try:
            result=subprocess.run([sys.executable,str(BASE/'build_single_notebook.py'),key],cwd=BASE,capture_output=True,timeout=30)
            if result.returncode:raise RuntimeError('No se pudo preparar el notebook privado; se restauro la configuracion.')
        except Exception:save_catalog(old);raise
        self.runtime.pop(key,None)
        self.log('Plantilla '+template['name']+' instalada en la configuracion y notebook privado. GPU sin iniciar; los pesos se descargan al encender.')
        self.log('Prepara de nuevo el paquete de clientes para actualizar contexto y nombre.')
    def credentials(self,key,data):
        username=str(data.get('username','')).strip();secret=str(data.get('key_value','')).strip()
        if (not secret.startswith('KGAT_') and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{1,63}',username)) or not 16<=len(secret)<=2048 or any(c.isspace() for c in secret):raise ValueError('Pega un token KGAT_ o carga el JSON legacy que incluye usuario y key.')
        credentials={'username':username,'api_token' if secret.startswith('KGAT_') else 'key':secret}
        check=subprocess.run([sys.executable,str(BASE/'credential_check.py')],input=json.dumps(credentials),capture_output=True,text=True,encoding='utf8',timeout=40)
        if check.returncode:raise ValueError('Kaggle no valido estas credenciales. No se modificaron las anteriores.')
        username=json.loads(check.stdout.strip().splitlines()[-1])['username'];credentials['username']=username
        config=catalog()
        for existing,p in config['profiles'].items():
            credential_path=BASE/f'kaggle({p["account"]}).json'
            if credential_path.exists() and json.loads(credential_path.read_text()).get('username')==username:
                if key is None:key=existing
                elif key!=existing:raise ValueError('Esta cuenta ya esta agregada. No se duplico.')
        if key is None:
            key=next((k for k,p in config['profiles'].items() if not (BASE/f'kaggle({p["account"]}).json').exists()),None)
            if key is None:raise ValueError('Ya estan configuradas las 8 conexiones admitidas por este relay. Usa API de Kaggle en una tarjeta para reemplazar una cuenta apagada.')
        p=config['profiles'][key];target=BASE/f'kaggle({p["account"]}).json'
        if target.exists():
            old=json.loads(target.read_text())
            if old['username']!=username:
                from coding_control import probe_state
                if probe_state(key) not in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'):raise ValueError('Confirma el apagado de la cuenta anterior antes de reemplazar su usuario.')
        temp=target.with_suffix('.pending');temp.write_text(json.dumps(credentials),encoding='utf8');temp.replace(target)
        config=catalog();profile=config['profiles'][key];profile['kernel_ref']=username+'/'+profile['kernel_ref'].split('/')[-1];profile['enabled']=True
        nickname=str(data.get('name','')).strip()
        if nickname and len(nickname)<=48 and not any(ord(c)<32 for c in nickname):profile['nickname']=nickname
        save_catalog(config);self.store.bind_identity(profile['account'],username);self.log('Cuenta '+username+' reconocida y guardada. No se inicio una GPU.')

def run():
    app=Dashboard()
    for profile in catalog()['profiles'].values():
        credential=BASE/f'kaggle({profile["account"]}).json'
        if credential.exists():app.store.bind_identity(profile['account'],json.loads(credential.read_text())['username'])
    gate=None
    from panel_auth import Sessions
    from http.cookies import SimpleCookie,CookieError
    sessions=Sessions()
    auth_transaction=threading.Lock()
    if os.environ.get('IA_SERVER_MODE')=='vps':
        from panel_auth import PasswordGate
        gate=PasswordGate(BASE/'.private/panel-auth.json')
    class Handler(BaseHTTPRequestHandler):
        def session(self):
            try:
                cookies=SimpleCookie(self.headers.get('Cookie',''));cookie=cookies.get(sessions.cookie_name)
                self.session_token=cookie.value if cookie else ''
            except CookieError:self.session_token=''
            return sessions.get(self.session_token)
        def redirect(self,location):
            self.send_response(303);self.send_header('Location',location);self.send_header('Cache-Control','no-store');self.end_headers()
        def send_page(self,page):
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' data: blob:; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");self.end_headers();self.wfile.write(page.encode())
        def authorized(self):
            if not panel_host(self.headers.get('Host',''),PORT):self.send_error(403);return False
            self.current_session=self.session() if gate else None
            if gate is not None and self.current_session is None:
                file_login=file_login_redirect(self.path,self.headers,self.command)
                if file_login:self.redirect(file_login)
                elif self.command in ('GET','HEAD') and not self.path.startswith('/api/') and self.path!='/health':self.redirect('/login')
                else:self.send_json(401,{'error':'Tu sesion termino. Ingresa nuevamente.'})
                return False
            return True
        def log_message(self,*args):pass
        def send_json(self,status,data):
            body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers()
            if self.command!='HEAD':self.wfile.write(body)
        def do_HEAD(self):
            if not panel_host(self.headers.get('Host',''),PORT):self.send_error(403);return
            if self.path.split('?')[0]=='/login':
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();return
            if self.path not in ('/','/health'):self.send_error(404);return
            if not self.authorized():return
            self.send_response(200);self.send_header('Cache-Control','no-store');self.end_headers()
        def do_GET(self):
            if self.path.split('?')[0]=='/login':
                if not panel_host(self.headers.get('Host',''),PORT):self.send_error(403);return
                if gate is None or self.session():
                    from urllib.parse import urlsplit,parse_qs
                    destination=parse_qs(urlsplit(self.path).query).get('next',['/'])[0]
                    self.redirect(login_return_target(destination));return
                login_file = (BASE/'web/login.html') if (BASE/'web/login.html').exists() else (BASE/'login.html')
                self.send_page(login_file.read_text(encoding='utf8'));return
            if not self.authorized():return
            if self.path=='/health':self.send_json(200,{'service':'kaggle-ia-panel'});return
            if self.path=='/api/templates':
                from templates import MODELS,TOOLS,WORKFLOWS,SOURCES
                self.send_json(200,{'models':MODELS,'tools':TOOLS,'workflows':WORKFLOWS,'sources':SOURCES,'verified_at':'2026-11-03'});return
            if self.path=='/api/state':self.send_json(200,app.state());return
            if self.path=='/api/session':self.send_json(200,{'username':self.current_session['username'] if self.current_session else 'Local','remote':gate is not None,'csrf':self.current_session['csrf'] if self.current_session else app.token});return
            assets={'/assets/design-system.css':('design-system.css','text/css'),'/assets/panel.css':('panel.css','text/css'),'/assets/dashboard.js':('dashboard.js','text/javascript'),'/assets/chat/workspace.js':('chat/workspace.js','text/javascript')}
            if self.path in assets:
                filename,mime=assets[self.path]
                asset_file=(BASE/'web'/filename) if (BASE/'web'/filename).exists() else (BASE/filename)
                raw=asset_file.read_bytes();self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
            if self.path.startswith('/api/download/'):
                download=self.path.removeprefix('/api/download/')
                with app.lock:path=app.downloads.get(download)
                if path is None or not path.is_file() or not path.resolve().is_relative_to((ROOT/'exportaciones').resolve()):self.send_error(404);return
                raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Disposition','attachment; filename="'+path.name+'"');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
            path_clean=self.path.split('?')[0]
            if path_clean=='/api/chat/storage':
                from chat_storage import storage_status,archived_items
                from chat_media import capabilities
                self.send_json(200,{'storage':storage_status(app.chat),'archived':archived_items(app.chat),'media':capabilities()});return
            if path_clean=='/api/chat/conversations':
                self.send_json(200,{'conversations':app.chat.list_conversations(),'limits':app.chat.limits()});return
            if path_clean.startswith('/api/chat/conversations/'):
                try:self.send_json(200,app.chat.get_conversation(path_clean.removeprefix('/api/chat/conversations/')))
                except ValueError as err:self.send_json(404,{'error':str(err)})
                return
            if path_clean.startswith('/api/chat/requests/'):
                try:self.send_json(200,app.chat.get_request(path_clean.removeprefix('/api/chat/requests/')))
                except ValueError as err:self.send_json(404,{'error':str(err)})
                return
            if path_clean.startswith('/api/chat/attachment/'):
                from urllib.parse import urlsplit,parse_qs
                query=parse_qs(urlsplit(self.path).query)
                attachment_id=path_clean.removeprefix('/api/chat/attachment/')
                if query.get('preview')==['1']:
                    try:self.send_json(200,app.chat.get_attachment_preview(attachment_id))
                    except ValueError:self.send_json(404,{'error':'Adjunto no encontrado.'})
                    return
                try:meta,path=app.chat.get_attachment_file(attachment_id)
                except ValueError:self.send_error(404);return
                inline=query.get('inline')==['1']
                response_mime,disposition=attachment_headers(meta['name'],meta['mime'],inline)
                raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type',response_mime);self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Disposition',disposition);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','private, max-age=3600');self.end_headers();self.wfile.write(raw);return
            if self.path!='/':self.send_error(404);return
            panel_file=(BASE/'web/panel.html') if (BASE/'web/panel.html').exists() else (BASE/'panel.html')
            page=panel_file.read_text(encoding='utf8').replace('__TOKEN__',self.current_session['csrf'] if self.current_session else app.token)
            self.send_page(page)
        def do_POST(self):
            if self.path=='/api/runtime':
                from inference_auth import allowed
                from operations import PHASES
                try:
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<2048:raise ValueError()
                    data=json.loads(self.rfile.read(length))
                    if not isinstance(data,dict):raise ValueError()
                    account=data.get('account')
                    key=next((k for k,p in catalog()['profiles'].items() if p['account']==account),None)
                    if key is None or not allowed(self.headers.get('Authorization',''),account,BASE/'.private/inference-auth.json'):self.send_error(401);return
                    if data.get('phase') not in PHASES or not re.fullmatch('[a-f0-9]{32}',data.get('session','')):raise ValueError()
                    reason=data.get('reason') if data.get('reason') in ('inactividad','limite de sesion','solicitado','error_runtime') else None
                    app.runtime[key]={'phase':data['phase'],'label':PHASES[data['phase']],'session':data['session'],'timestamp':time.time(),'reason':reason}
                    if reason:app.store.event('runtime_stop_'+reason,key,'error' if data['phase']=='failed' else 'done')
                    self.send_json(200,{'ok':True});return
                except (ValueError,TypeError,AttributeError):self.send_error(400);return
            login=self.path=='/api/login'
            if login:
                if gate is None:self.send_json(400,{'error':'El panel local no requiere login.'});return
                if not self.headers.get('Origin') or not mutation_allowed(ChainMap({'X-IA-Token':'login'},self.headers),'login',PORT):self.send_json(403,{'error':'Origen de acceso no permitido.'});return
            else:
                if not self.authorized():return
                csrf=self.current_session['csrf'] if self.current_session else app.token
                if not mutation_allowed(self.headers,csrf,PORT):self.send_json(403,{'error':'Origen o sesion no permitidos.'});return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send_error(415);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=(4096 if self.path in ('/api/login','/api/password') else 24*1024*1024):raise ValueError('Solicitud demasiado grande o vacia.')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('Se esperaba un objeto JSON.')
                if self.path=='/api/refresh':app.refresh_trigger.set();self.send_json(202,{'accepted':True});return
                if self.path=='/api/diagnose':
                    from operations import diagnostic
                    key=data.get('key');config=catalog()
                    if key not in config['profiles']:raise ValueError('Cuenta invalida.')
                    p=config['profiles'][key];snapshot=next(a for a in app.state()['accounts'] if a['key']==key)
                    connection=json.loads((BASE/'.private/api-clients.json').read_text())[str(p['account'])]
                    try:code=requests.get(connection['url']+'/models',headers={'Authorization':'Bearer '+connection['token']},timeout=10).status_code
                    except requests.RequestException:code=0
                    try:resident=any(m.get('name','').split(':')[0]==p['model'] for m in requests.get('http://127.0.0.1:'+str(p['port'])+'/api/ps',timeout=3).json().get('models',[]))
                    except (requests.RequestException,ValueError):resident=False
                    self.send_json(200,{'state':snapshot['state'],'api_status':code,'model_loaded':resident,'message':diagnostic(snapshot['state'],code,resident),'paseo':'En la PC: ABRIR_PASEO.bat comprueba el daemon. El servidor no puede inspeccionar tu escritorio.'});return
                if self.path=='/api/tool-package':
                    from tool_templates import build_tool_package
                    key=data.get('key');config=catalog()
                    if not isinstance(key,str) or key not in config['profiles']:raise ValueError('Cuenta invalida.')
                    p=config['profiles'][key]
                    if not (BASE/f'kaggle({p["account"]}).json').exists():raise ValueError('Agrega primero la API de esta cuenta.')
                    connection=json.loads((BASE/'.private/api-clients.json').read_text())[str(p['account'])]
                    download=uuid.uuid4().hex
                    package=build_tool_package(data.get('tool'),p,connection,ROOT/'exportaciones'/('herramienta-PRIVADA-'+download+'.zip'))
                    with app.lock:app.downloads[download]=package
                    app.store.event('tool_package',key,'done')
                    self.send_json(200,{'download':{'id':download,'filename':package.name,'private':True}});return
                if self.path=='/api/client-config':
                    from client_configs import build_configs,CLIENT_LAUNCHERS
                    from portability import export_program
                    import zipfile
                    key=data.get('key');config=catalog()
                    if not isinstance(key,str) or key not in config['profiles']:raise ValueError('Selecciona una cuenta valida.')
                    profile=config['profiles'][key]
                    credentials_path=BASE/'.private/api-clients.json'
                    if not credentials_path.exists():raise ValueError('Falta provisionar las claves HTTPS de los clientes en el servidor.')
                    connections=json.loads(credentials_path.read_text(encoding='utf8'));connection=connections[str(profile['account'])]
                    snippets=build_configs(profile,connection)
                    required=[BASE/'configure_clients.py',BASE/'instalar.ps1']
                    if any(not p.is_file() for p in required):raise ValueError('El instalador de clientes esta incompleto en el servidor; no se genero un paquete incompleto.')
                    download=uuid.uuid4().hex;folder=ROOT/'exportaciones';folder.mkdir(exist_ok=True)
                    package=export_program(ROOT,folder/('configuracion-clientes-PRIVADA-'+download[:12]+'.zip'))
                    config['selected']=key
                    with zipfile.ZipFile(package,'a',zipfile.ZIP_DEFLATED) as archive:
                        existing=set(archive.namelist())
                        for name,content in CLIENT_LAUNCHERS.items():
                            if name not in existing:archive.writestr(name,content)
                        archive.writestr('sistema/model_profiles.json',json.dumps(config,ensure_ascii=False,indent=2))
                        archive.writestr('sistema/.private/api-clients.json',json.dumps(connections))
                        archive.writestr('sistema/.private/panel-remote.json',json.dumps({'url':os.environ.get('IA_PUBLIC_ORIGIN','https://ia.example.com')}))
                    package.chmod(0o600)
                    with app.lock:app.downloads[download]=package
                    app.store.event('client_config',key,'done')
                    self.send_json(200,{'profile_key':key,'configs':snippets,'url':connection['url'],'api_key':connection['token'],'model':profile['model'],'context':profile['context'],'provider':profile['provider_id']+'/'+profile['model'],'download':{'id':download,'filename':package.name,'private':True}});return
                source=self.headers.get('X-IA-Client-IP',self.client_address[0])
                if login:
                    with auth_transaction:
                        if not gate.check(data.get('username'),data.get('password'),source):self.send_json(401,{'error':'Usuario o contrasena incorrectos. Si hubo varios intentos, espera un minuto.'});return
                        previous=self.session_token if self.session() else ''
                        sessions.revoke(previous)
                        token=sessions.create(gate.record['username'])
                    self.send_response(200);self.send_header('Set-Cookie',sessions.cookie(token));self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(json.dumps({'ok':True,'redirect':login_return_target(data.get('next','/'))}).encode());return
                if self.path in ('/api/logout','/api/password'):
                    if gate is None:self.send_json(400,{'error':'Accion disponible en el panel remoto.'});return
                    if self.path=='/api/password':
                        with auth_transaction:
                            if not gate.change_password(data.get('current'),data.get('password'),source):self.send_json(403,{'error':'La contrasena actual no es correcta.'});return
                            sessions.clear()
                    else:sessions.revoke(self.session_token)
                    self.send_response(200);self.send_header('Set-Cookie',sessions.cookie(''));self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b'{"ok":true}');return
                if self.path=='/api/chat/storage':
                    from chat_storage import save_policy
                    self.send_json(200,save_policy(app.chat,data.get('maximum_mb',512),data.get('retention_days',30)));return
                if self.path=='/api/chat/retention':
                    from chat_storage import archive_stale
                    self.send_json(200,archive_stale(app.chat));return
                if self.path=='/api/chat/restore':
                    from chat_storage import restore
                    self.send_json(200,restore(app.chat,data.get('kind'),data.get('id')));return
                if self.path=='/api/chat/conversations':
                    account=data.get('account') or catalog().get('selected','rapido')
                    if account not in catalog()['profiles']:raise ValueError('Cuenta invalida.')
                    self.send_json(200,app.chat.create_conversation(account,data.get('title',''),data.get('system_prompt','')));return
                if self.path=='/api/chat/rename':
                    account=data.get('account')
                    if account is not None and account not in catalog()['profiles']:raise ValueError('Cuenta invalida.')
                    self.send_json(200,app.chat.update_conversation(data.get('id',''),data.get('title'),data.get('system_prompt'),account));return
                if self.path=='/api/chat/delete':
                    self.send_json(200,app.chat.archive_conversation(data.get('id','')));return
                if self.path=='/api/chat/upload':
                    self.send_json(200,app.chat.upload_attachment(data.get('conversation',''),data.get('name','archivo'),data.get('mime','application/octet-stream'),data.get('data','')));return
                if self.path=='/api/chat/send':
                    cid=data.get('conversation','')
                    conv=app.chat.get_conversation(cid)['conversation']
                    key=data.get('account') or conv['account']
                    profiles=catalog()['profiles']
                    if key not in profiles:raise ValueError('Cuenta invalida.')
                    if key!=conv['account']:app.chat.update_conversation(cid,account=key)
                    profile=profiles[key]
                    effort=data.get('reasoning_effort')
                    if effort in ('none','low','medium','xhigh'):
                        profile={**profile,'effort':effort}
                    self.send_json(200,app.chat.start_send(cid,data.get('content',''),data.get('attachments',[]),profile,data.get('temperature'),data.get('max_tokens')));return
                if self.path=='/api/chat/cancel':
                    self.send_json(200,app.chat.cancel_request(data.get('request_id','')));return
                if self.path=='/api/chat/export':
                    cid=data.get('id','');download=uuid.uuid4().hex;folder=ROOT/'exportaciones';folder.mkdir(exist_ok=True)
                    package=app.chat.export_zip(cid,folder/('chat-PRIVADO-'+download[:12]+'.zip'))
                    with app.lock:app.downloads[download]=package
                    self.send_json(200,{'download':{'id':download,'filename':package.name,'private':True}});return
                if self.path=='/api/model/inspect':self.send_json(200,inspect_model(data.get('repo','')));return
                if self.path!='/api/action':self.send_error(404);return
                app.begin(data);self.send_json(202,{'accepted':True})
            except (ValueError,requests.RequestException) as error:self.send_json(400,{'error':str(error)[:240]})
    servers=[]
    try:
        servers.append(ThreadingHTTPServer(('127.0.0.1',PORT),Handler))
        for account,proxy,backend in [(1,19134,18134)] + [(i, 19860 + (i - 2), 17860 + (i - 2)) for i in range(2, 9)]:servers.append(create_proxy(account,proxy,backend,app.store,BASE/'.private/inference-auth.json'))
        servers.append(create_pool_proxy(19000,app.store,BASE/'.private/inference-auth.json',catalog_fn=catalog))
        for server in servers[1:]:threading.Thread(target=server.serve_forever,daemon=True).start()
        threading.Thread(target=app.monitor,daemon=True).start()
        servers[0].serve_forever()
    finally:
        for server in servers:server.server_close()
if __name__=='__main__':run()
