"""Create a reviewable public tree, scanning it against locally held secrets."""
import json,time,zipfile
from pathlib import Path
from portability import export_program

def prepare(root):
    root=Path(root).resolve();folder=root/'exportaciones';folder.mkdir(exist_ok=True)
    archive=export_program(root,folder/'kaggle-ia-publico.zip')
    secrets=[]
    for path in (root/'sistema').glob('kaggle(*).json'):
        data=json.loads(path.read_text(encoding='utf8'))
        secrets.extend(v.encode() for k,v in data.items() if k in ('key','api_token') and isinstance(v,str) and len(v)>12)
    private=root/'sistema/.private'
    clients=private/'api-clients.json'
    if clients.exists():secrets.extend(v['token'].encode() for v in json.loads(clients.read_text()).values())
    key=private/'kaggle_relay'
    if key.exists():secrets.append(key.read_bytes().strip())
    access=private/'ACCESO_PANEL.txt'
    if access.exists():
        secrets.extend(line.split(': ',1)[1].encode() for line in access.read_text().splitlines() if line.startswith('Contrasena: '))
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if '.private' in name or 'kaggle(' in name or name.endswith('.ipynb'):raise RuntimeError('Exportacion contiene un archivo privado; no publicar.')
            raw=z.read(name)
            if any(secret in raw for secret in secrets) or (b'-----BEGIN '+b'OPENSSH PRIVATE KEY-----') in raw:raise RuntimeError('La exportacion contiene un secreto; no publicar.')
        destination=folder/'github-listo'
        if destination.exists():
            existing={p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
            if existing-set(z.namelist()) or any(p.is_symlink() for p in destination.rglob('*')):raise RuntimeError('La carpeta publica contiene archivos ajenos; conservada sin cambios.')
        destination.mkdir(exist_ok=True);z.extractall(destination)
    print('Exportacion publica verificada contra las claves locales.')
    print('Carpeta:',destination);print('ZIP:',archive)
    return destination
if __name__=='__main__':prepare(Path(__file__).resolve().parent.parent)
