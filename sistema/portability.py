"""Export executable sources without keys; private backups use a strict allowlist."""
import json,zipfile,os
from pathlib import Path

PRIVATE_FILES={'sistema/kaggle(1).json','sistema/kaggle(2).json',
               'sistema/.private/kaggle_relay','sistema/.private/known_hosts',
               'sistema/.private/connection.json','sistema/model_profiles.json'}
PRIVATE_FILES.update({'sistema/.private/panel-remote.json','sistema/.private/api-clients.json','sistema/.private/inference-auth.json'})
MAX_FILE=2*1024*1024

def export_program(root,destination):
    root=Path(root).resolve();destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    files=[p for p in root.iterdir() if p.is_file() and (p.suffix=='.bat' or p.name in ('README.md','.gitignore'))]
    system=root/'sistema'
    if system.exists():files.extend(p for p in system.iterdir() if p.is_file() and (p.suffix in ('.py','.ps1','.bat','.html','.css','.js') or p.name in ('requirements.txt','requirements.lock.txt','requirements-asr.txt','model_profiles.example.json')))
    fonts=system/'fonts'
    if fonts.exists():files.extend(p for p in fonts.iterdir() if p.is_file() and p.name in ('Geist-Variable.ttf','OFL.txt'))
    for directory in ('deployment','docs/manual','.github'):
        folder=root/directory
        if folder.exists():files.extend(p for p in folder.rglob('*') if p.is_file() and (p.suffix in ('.md','.sh','.service','.yml','.conf') or p.name=='Caddyfile'))
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.resolve().is_relative_to(root):
                name=path.relative_to(root).as_posix()
                if path.suffix=='.sh':archive.writestr(name,path.read_bytes().replace(b'\r\n',b'\n'))
                else:archive.write(path,name)
        profile=system/'model_profiles.json'
        if profile.exists():
            data=json.loads(profile.read_text(encoding='utf8'))
            for item in data.get('profiles',{}).values():
                item['kernel_ref']='CONFIGURAR_USUARIO/'+item['kernel_ref'].split('/')[-1]
                item.pop('previous_kernel_ref',None)
                item.pop('cache_source',None)
            if 'sistema/model_profiles.example.json' not in archive.namelist():archive.writestr('sistema/model_profiles.example.json',json.dumps(data,ensure_ascii=False,indent=2))
    return destination

def export_private(root,destination):
    root=Path(root).resolve();destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(PRIVATE_FILES):
            path=root/name
            if path.is_file() and path.resolve().is_relative_to(root):archive.write(path,name)
    return destination

def import_private(root,source):
    root=Path(root).resolve()
    with zipfile.ZipFile(source) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise ValueError('Respaldo con archivos duplicados')
        if any(n not in PRIVATE_FILES for n in names):raise ValueError('El ZIP contiene rutas no permitidas')
        if any(i.file_size>MAX_FILE for i in archive.infolist()):raise ValueError('Archivo privado demasiado grande')
        payload={name:archive.read(name) for name in names}
        for name,raw in payload.items():
            if name.endswith('.json'):
                data=json.loads(raw)
                if 'kaggle(' in name and not (isinstance(data.get('username'),str) and isinstance(data.get('key',data.get('api_token')),str)):
                    raise ValueError('Credencial Kaggle invalida')
                if name=='sistema/model_profiles.json':
                    expected={'rapido':(1,18134,'text','kernel'),'coder2':(2,17860,'coding2','kernel2')}
                    if set(data.get('profiles',{}))!=set(expected) or data.get('selected') not in expected:raise ValueError('Catalogo de conexion invalido')
                    for key,values in expected.items():
                        p=data['profiles'][key]
                        if tuple(p.get(f) for f in ('account','port','relay_role','kernel_dir'))!=values:raise ValueError('El respaldo cambia rutas o puertos restringidos')
        # Validate everything before touching destination files.
        for name,raw in payload.items():
            target=root/name
            if not target.resolve().is_relative_to(root):raise ValueError('Destino fuera de la instalacion')
        for name,raw in payload.items():
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            tmp=target.with_name(target.name+'.importing');tmp.write_bytes(raw);tmp.replace(target)
            if name.endswith('kaggle_relay'):os.chmod(target,0o600)
    return len(payload)
