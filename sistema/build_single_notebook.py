"""Build the one private coding notebook; generated file contains the restricted SSH key."""
import json,sys,textwrap
from pathlib import Path

BASE=Path(__file__).resolve().parent
from connection import settings
from cpu_cache import source_for,CACHE_READER
relay_config=settings()
profile_key=sys.argv[1] if len(sys.argv)>1 else 'rapido'
profile=json.loads((BASE/'model_profiles.json').read_text(encoding='utf8'))['profiles'][profile_key]
cache=source_for(profile)
if cache is None:profile.pop('cache_source',None)
port=profile.get('port',18134)
key=(BASE/'.private/kaggle_relay').read_text()
hosts=(BASE/'.private/known_hosts').read_text()
vision_helper=(BASE/'vision_helper.py').read_text(encoding='utf8')+'\n'
gateway=vision_helper+(BASE/'remote_gateway.py').read_text(encoding='utf8').replace('18134',str(port))
cells=[]
def code(source):
    if cells:
        source='try:\n'+textwrap.indent(source,'    ')+"\nexcept Exception:\n    report_phase('failed','error_runtime')\n    raise\n"
    compile(source,'<notebook-cell>','exec')
    cells.append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':source.splitlines(True)})

telemetry_path=BASE/'.private/api-clients.json'
telemetry=json.loads(telemetry_path.read_text()).get(str(profile['account']),{}) if telemetry_path.exists() else {}
telemetry_url=relay_config.get('panel_url','https://ia.example.com')+'/api/runtime'
bootstrap="import requests,uuid,time\n_allocation_started=time.monotonic()\n_runtime_session=uuid.uuid4().hex\ndef report_phase(phase,reason=None):\n    try: requests.post("+repr(telemetry_url)+",json={'account':"+str(profile['account'])+",'phase':phase,'session':_runtime_session,'reason':reason},headers={'Authorization':'Bearer '+"+repr(telemetry.get('token',''))+"},timeout=3)\n    except Exception: pass\nreport_phase('assigned')\n"
code(bootstrap)
code('''import os, sys, time, subprocess, json, threading
from pathlib import Path
import requests
print('GPU asignada por Kaggle:',flush=True)
gpu_probe=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True,check=True)
print(gpu_probe.stdout,flush=True)
runtime_fingerprint={'python':sys.version.split()[0],'gpu':gpu_probe.stdout.strip().splitlines(),'cuda_runtime_env':os.environ.get('CUDA_VERSION'),'flash_attention_requested':True,'kv_cache_requested':'q8_0'}
''')
code("report_phase('install')\n"+'''print('Instalando servidor privado de codigo...',flush=True)
import shutil,importlib.util
needed=[package for command,package in [('zstd','zstd'),('lspci','pciutils'),('lshw','lshw'),('ssh','openssh-client')] if not shutil.which(command)]
if needed:
    subprocess.run(['apt-get','update','-qq'],check=True)
    subprocess.run(['apt-get','install','-y','-qq',*needed],check=True)
missing=[name for name in ('huggingface_hub','requests') if importlib.util.find_spec(name) is None]
if missing:subprocess.run([sys.executable,'-m','pip','install','-q',*missing],check=True)
subprocess.run('curl -fsSL https://ollama.com/install.sh | sh',shell=True,check=True,env={**os.environ,'OLLAMA_VERSION':'0.40.13'})
''')
code("report_phase('download')\n"+'''from huggingface_hub import hf_hub_download
'''+f'config={profile!r}\n'+CACHE_READER+'''
# Scratch storage: model weights are not copied into notebook outputs or /root.
os.makedirs('/kaggle/temp/coder-weights',exist_ok=True)
print('Descargando UNICAMENTE '+config['label']+'...',flush=True)
model_path=find_cached_weights(config)
if model_path:
    runtime_fingerprint['weights_source']='mounted-cache-sha256-verified'
    print('Pesos montados verificados; sin descarga externa.',flush=True)
else:
    model_path=hf_hub_download(config['repo'],config['filename'],revision=config['revision'],local_dir='/kaggle/temp/coder-weights')
    runtime_fingerprint['weights_source']='huggingface-download'
print('Pesos descargados.',flush=True)
''')
code(r'''os.environ.update(OLLAMA_HOST='127.0.0.1:11434',OLLAMA_MODELS='/kaggle/temp/ollama_models',OLLAMA_NUM_PARALLEL='1',OLLAMA_FLASH_ATTENTION='1',OLLAMA_KV_CACHE_TYPE='q8_0',CUDA_VISIBLE_DEVICES='0,1')
os.makedirs(os.environ['OLLAMA_MODELS'],exist_ok=True)
ollama_log=open('/tmp/ollama.log','w')
proc_ollama=subprocess.Popen(['ollama','serve'],stdout=ollama_log,stderr=ollama_log)
for _ in range(60):
    try:
        if requests.get('http://127.0.0.1:11434/api/version',timeout=2).ok:break
    except requests.RequestException:pass
    time.sleep(1)
else:raise RuntimeError('Ollama no inicio')
runtime_fingerprint['ollama_version']=requests.get('http://127.0.0.1:11434/api/version',timeout=5).json().get('version')
runtime_fingerprint['engine_started_elapsed_seconds']=round(time.monotonic()-_allocation_started,1)
modelfile='FROM '+model_path+'\n'
parameters={'num_gpu':99,'num_ctx':config['context'],'temperature':config['temperature'],**config.get('parameters',{})}
modelfile+=''.join('PARAMETER '+k+' '+str(v)+'\n' for k,v in parameters.items())
Path('/tmp/Modelfile').write_text(modelfile)
report_phase('register')
subprocess.run(['ollama','create',config['model'],'-f','/tmp/Modelfile'],check=True)
print('Modelo de codigo registrado.',flush=True)
''')
code(f"relay_config={relay_config!r}\nPath('/tmp/relay_key').write_text({key!r})\nPath('/tmp/relay_hosts').write_text({hosts!r})\nos.chmod('/tmp/relay_key',0o600)\n"+gateway+'''
relay_log=open('/tmp/relay.log','w')
proc_ssh=subprocess.Popen(['ssh','-N','-T','-o','BatchMode=yes','-i','/tmp/relay_key','-o','UserKnownHostsFile=/tmp/relay_hosts','-o','StrictHostKeyChecking=yes','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-R','127.0.0.1:18134:127.0.0.1:18134','-p',str(relay_config['port']),relay_config['user']+'@'+relay_config['host']],stdout=relay_log,stderr=relay_log)
time.sleep(3)
if proc_ssh.poll() is not None:raise RuntimeError('No se pudo iniciar el relay SSH')
print('RELAY_READY',flush=True)
print('Cargando modelo en las T4...',flush=True)
report_phase('warm')
r=requests.post('http://127.0.0.1:11434/api/chat',json={'model':config['model'],'messages':[{'role':'user','content':'Responde LISTO'}],'think':False,'stream':False,'keep_alive':-1,'options':{'num_predict':64}},timeout=600)
r.raise_for_status()
if not r.json().get('message',{}).get('content'):raise RuntimeError('No se confirmo una respuesta del modelo')
print('MODEL_READY',flush=True)
runtime_fingerprint['ready_elapsed_seconds']=round(time.monotonic()-_allocation_started,1)
report_phase('ready')
'''.replace('127.0.0.1:18134',f'127.0.0.1:{port}'))
code((BASE/'lifecycle.py').read_text(encoding='utf8')+'''
session_started=_allocation_started
idle_policy=config.get('idle_minutes',15)
maximum_policy=config.get('max_session_minutes',120)
with lock:last_activity=session_started
try:
    while not stop_event.wait(5):
        if proc_ollama.poll() is not None:raise RuntimeError('Ollama termino')
        if proc_ssh.poll() is not None:
            for attempt in range(3):
                proc_ssh=subprocess.Popen(proc_ssh.args,stdout=relay_log,stderr=relay_log)
                time.sleep(5)
                if proc_ssh.poll() is None:break
            else:raise RuntimeError('No se recupero SSH')
        with lock:
            reason=stop_reason(session_started,last_activity,active_requests,time.monotonic(),config.get('idle_minutes',15),config.get('max_session_minutes',120)+session_extension)
        if reason:
            print('Apagado automatico: '+reason,flush=True)
            break
finally:
    report_phase('stopped',reason if 'reason' in globals() and reason else 'solicitado')
    server.shutdown()
    for proc in (proc_ssh,proc_ollama):
        proc.terminate()
        try:proc.wait(timeout=15)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
print('STOPPED: procesos terminados',flush=True)
''')
target=BASE/profile.get('kernel_dir','kernel');target.mkdir(exist_ok=True)
(target/'coder_server.ipynb').write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':4},ensure_ascii=False,indent=2),encoding='utf8')
kernel_ref=profile.get('previous_kernel_ref') if '--replace-media' in sys.argv else profile['kernel_ref']
metadata={'id':kernel_ref,'title':profile['kernel_title'],'code_file':'coder_server.ipynb','language':'python','kernel_type':'notebook','is_private':'true','enable_gpu':'true','enable_internet':'true','enable_tpu':'false','machine_shape':'NvidiaTeslaT4','dataset_sources':[],'competition_sources':[],'kernel_sources':[cache['kernel_ref']] if cache else [],'model_sources':[]}
(target/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
print('Notebook de modelo unico generado y sintaxis validada. Mantener privado.')
