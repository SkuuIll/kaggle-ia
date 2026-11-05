"""Prepare private CPU-only weight caches; never starts a GPU or downloads weights locally."""
import hashlib,json,re,sys,time
from pathlib import Path,PurePosixPath
import requests

TERMINAL={'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'}
MAX_CACHE_BYTES=18*1024**3

def expected_artifact(profile):
    filename=profile['filename']
    if not filename.endswith('.gguf') or PurePosixPath(filename).is_absolute() or '..' in PurePosixPath(filename).parts or '\\' in filename:raise ValueError('Archivo de pesos inválido.')
    r=requests.get('https://huggingface.co/api/models/'+profile['repo']+'/revision/'+profile['revision'],params={'blobs':'true'},timeout=30)
    r.raise_for_status();d=r.json()
    if d.get('sha')!=profile['revision']:raise ValueError('La revisiÃ³n de pesos no coincide.')
    f=next((f for f in d.get('siblings',[]) if f.get('rfilename')==profile['filename']),None)
    if not f or not isinstance(f.get('size'),int) or not 0<f['size']<=MAX_CACHE_BYTES:raise ValueError('Este archivo no cabe con margen en la salida de cachÃ© CPU (mÃ¡ximo18GiB).')
    sha=f.get('lfs',{}).get('sha256')
    if not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('No hay un SHA256 verificable para estos pesos.')
    return {k:profile[k] for k in ('repo','revision','filename')}|{'size_bytes':f['size'],'sha256':sha,'schema':1}

def validate_manifest(manifest,expected):
    if not isinstance(manifest,dict) or any(manifest.get(k)!=v for k,v in expected.items()):raise ValueError('La cachÃ© no corresponde al modelo, revisiÃ³n o integridad esperados.')
    return manifest

def source_for(profile):
    value=profile.get('cache_source')
    if not isinstance(value,dict):return None
    owner=profile['kernel_ref'].split('/')[0]
    if not re.fullmatch(re.escape(owner)+r'/ia-weights-cache-[a-f0-9]{12}',value.get('kernel_ref','')):raise ValueError('La cachÃ© debe pertenecer a esta cuenta.')
    if any(value.get(k)!=profile[k] for k in ('repo','revision','filename')):return None
    if not re.fullmatch('[a-f0-9]{64}',value.get('sha256','')) or not 0<value.get('size_bytes',0)<=MAX_CACHE_BYTES:raise ValueError('Integridad de cachÃ© invÃ¡lida.')
    return value

def prepare(profile,key,base):
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}',key):raise ValueError('Identificador de cuenta inválido.')
    expected=expected_artifact(profile)
    digest=hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()[:12]
    slug='ia-weights-cache-'+digest;ref=profile['kernel_ref'].split('/')[0]+'/'+slug
    folder=Path(base)/'.private/cpu-cache'/key;folder.mkdir(parents=True,exist_ok=True)
    source="""import hashlib,json,os,subprocess,sys,shutil
from pathlib import Path
if not __import__('importlib.util',fromlist=['find_spec']).find_spec('huggingface_hub'):
    subprocess.run([sys.executable,'-m','pip','install','-q','huggingface_hub'],check=True)
from huggingface_hub import hf_hub_download
"""+'expected='+repr(expected)+'\n'+"""root=Path('/kaggle/working')
if shutil.disk_usage(root).free < expected['size_bytes']+1024**3:raise RuntimeError('No hay espacio suficiente para preparar los pesos.')
path=Path(hf_hub_download(expected['repo'],expected['filename'],revision=expected['revision'],local_dir=str(root)))
h=hashlib.sha256()
with path.open('rb') as stream:
    for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
if path.stat().st_size!=expected['size_bytes'] or h.hexdigest()!=expected['sha256']:raise RuntimeError('La integridad de los pesos no coincide.')
(root/'manifest.json').write_text(json.dumps(expected),encoding='utf8')
print('CACHE_READY: integridad verificada, sin GPU.')
"""
    compile(source,'cache_cpu.py','exec');(folder/'cache_cpu.py').write_text(source,encoding='utf8')
    metadata={'id':ref,'title':slug,'code_file':'cache_cpu.py','language':'python','kernel_type':'script','is_private':'true','enable_gpu':'false','enable_tpu':'false','enable_internet':'true','dataset_sources':[],'competition_sources':[],'kernel_sources':[],'model_sources':[]}
    (folder/'kernel-metadata.json').write_text(json.dumps(metadata),encoding='utf8')
    info={'kernel_ref':ref,'expected':expected,'prepared_at':time.time()}
    (folder/'cache-info.json').write_text(json.dumps(info),encoding='utf8')
    return info,folder

def launch(profile,key,base,client):
    info,folder=prepare(profile,key,base)
    from coding_control import state
    current=state(client,info['kernel_ref'])
    if current in ('RUNNING','QUEUED','COMPLETE'):return info|{'state':current,'started':False}
    client.kernels_push(str(folder),timeout='1800')
    return info|{'state':'SUBMITTED_CPU','started':True}

def status(profile,key,base,client,attach=False):
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}',key):raise ValueError('Identificador de cuenta inválido.')
    folder=Path(base)/'.private/cpu-cache'/key;path=folder/'cache-info.json'
    if not path.exists():return {'state':'NOT_PREPARED','attached':False}
    info=json.loads(path.read_text());expected=info['expected']
    if any(expected.get(k)!=profile[k] for k in ('repo','revision','filename')):return {'state':'STALE','attached':False}
    current=str(client.kernels_status(info['kernel_ref']).status).upper().split('.')[-1]
    result={'state':current,'kernel_ref':info['kernel_ref'],'attached':bool(source_for(profile)),'size_bytes':expected['size_bytes']}
    if current=='COMPLETE':
        manifest_dir=folder/'manifest';manifest_dir.mkdir(exist_ok=True)
        (manifest_dir/'manifest.json').unlink(missing_ok=True)
        client.kernels_output(info['kernel_ref'],path=str(manifest_dir),file_pattern=r'^manifest\.json$',force=True,quiet=True)
        manifest=manifest_dir/'manifest.json'
        if not manifest.is_file():raise ValueError('La ejecuciÃ³n CPU terminÃ³, pero falta el manifiesto de integridad.')
        validate_manifest(json.loads(manifest.read_text()),expected)
        result['verified']=True
        if attach:
            profile['cache_source']=expected|{'kernel_ref':info['kernel_ref']};result['attached']=True
    elif attach:raise ValueError('La cachÃ© todavÃ­a no estÃ¡ completa; no se adjuntÃ³ al arranque.')
    return result

# Self-contained reader embedded in future private GPU notebooks.
CACHE_READER=r"""import hashlib,json
from pathlib import Path
def find_cached_weights(config):
    source=config.get('cache_source')
    if not source:return None
    manifests=list(Path('/kaggle/input').glob('**/manifest.json'))
    for manifest in manifests:
        try:data=json.loads(manifest.read_text())
        except (OSError,ValueError):continue
        if any(data.get(k)!=source.get(k) for k in ('repo','revision','filename','size_bytes','sha256','schema')):continue
        candidate=(manifest.parent/source['filename']).resolve()
        if not candidate.is_relative_to(manifest.parent.resolve()) or not candidate.is_file():continue
        if candidate.stat().st_size!=source['size_bytes']:continue
        digest=hashlib.sha256()
        with candidate.open('rb') as stream:
            for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
        if digest.hexdigest()!=source['sha256']:raise RuntimeError('La cachÃ© montada fallÃ³ su verificaciÃ³n SHA256.')
        return str(candidate)
    raise RuntimeError('Se configurÃ³ una cachÃ©, pero no estÃ¡ montada o no coincide. RevisÃ¡ su estado antes de iniciar otra sesiÃ³n.')
"""
