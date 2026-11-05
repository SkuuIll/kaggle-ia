"""Provision a pinned multilingual Whisper CPU model from its official repository."""
import hashlib,json,os
from pathlib import Path
import requests

REPO='Systran/faster-whisper-tiny'
REVISION='d90ca5fe260221311c53c58e660288d3deb8d356'
FILES=('config.json','model.bin','tokenizer.json','vocabulary.txt')
WEIGHT_SHA256='dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1'

def prepare(base):
    folder=Path(base)/'.private/asr-models/faster-whisper-tiny'/REVISION
    folder.mkdir(parents=True,exist_ok=True)
    response=requests.get(f'https://huggingface.co/api/models/{REPO}/revision/{REVISION}',params={'blobs':'true'},timeout=30)
    response.raise_for_status();metadata=response.json()
    if metadata.get('sha')!=REVISION:raise ValueError('La revisión ASR no coincide.')
    manifest={'repo':REPO,'revision':REVISION,'device':'cpu','compute_type':'int8','files':{}}
    for name in FILES:
        info=next((f for f in metadata['siblings'] if f['rfilename']==name),None)
        if not info or not 0<info.get('size',0)<=80*1024*1024:raise ValueError('Archivo ASR inválido.')
        target=folder/name;part=folder/(name+'.part')
        digest=hashlib.sha256();git=hashlib.sha1();git.update(b'blob '+str(info['size']).encode()+b'\0');size=0
        try:
            with requests.get(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}',stream=True,timeout=(20,120)) as download:
                download.raise_for_status()
                with part.open('wb') as out:
                    for chunk in download.iter_content(1024*1024):
                        size+=len(chunk)
                        if size>info['size']:raise ValueError('El archivo ASR supera el tamaño esperado.')
                        out.write(chunk);digest.update(chunk);git.update(chunk)
            expected=info.get('lfs',{}).get('sha256')
            if size!=info['size'] or (expected and digest.hexdigest()!=expected):raise ValueError('Falló la integridad ASR.')
            if name=='model.bin' and digest.hexdigest()!=WEIGHT_SHA256:raise ValueError('El modelo ASR no coincide con el hash fijado.')
            if not expected and git.hexdigest()!=info.get('blobId'):raise ValueError('El archivo de configuración ASR no coincide con su revisión.')
            part.replace(target);target.chmod(0o600)
            manifest['files'][name]={'size':size,'sha256':digest.hexdigest()}
        finally:part.unlink(missing_ok=True)
    path=folder/'manifest.json';path.write_text(json.dumps(manifest,indent=2),encoding='utf8');path.chmod(0o600)
    return folder

if __name__=='__main__':
    result=prepare(Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name=='chat' else Path(__file__).resolve().parent)
    print('Modelo ASR local preparado y verificado: '+REPO+' @ '+REVISION)
