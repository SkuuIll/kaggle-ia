"""Model selection validation; routing and aliases stay stable per account."""
import json,re
from pathlib import Path
from urllib.parse import urlparse
def parse_repo(value):
    value=value.strip()
    if '://' in value:
        url=urlparse(value)
        if url.scheme!='https' or url.netloc not in ('huggingface.co','www.huggingface.co') or url.query or url.fragment:
            raise ValueError('Usa una URL publica de huggingface.co sin tokens ni parametros.')
        value='/'.join(url.path.strip('/').split('/')[:2])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,255}',value):
        raise ValueError('Repositorio invalido; usa autor/modelo.')
    return value
def update_model(path,key,repo,filename,revision,context,stopped):
    if not stopped:raise ValueError('Primero hay que confirmar la parada en Kaggle.')
    repo=parse_repo(repo);context=int(context)
    if not 4096<=context<=1048576:raise ValueError('Contexto fuera de rango: 4096 a1048576.')
    if not re.fullmatch(r'[a-f0-9]{40,64}',revision):raise ValueError('Revision de Hugging Face invalida.')
    if not filename.endswith('.gguf') or filename.startswith(('/','\\')) or '..' in Path(filename).parts or '\\' in filename:
        raise ValueError('Archivo GGUF invalido.')
    path=Path(path);data=json.loads(path.read_text(encoding='utf8'));profile=data['profiles'][key]
    profile.pop('template_id',None)
    profile.pop('engine',None)
    profile.update(repo=repo,filename=filename,revision=revision,context=context,source=None,
                   label=repo.split('/')[-1].removesuffix('-GGUF')+f' - {context//1024}k (cuenta {profile["account"]})',
                   parameters={'draft_num_predict':0})
    tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(path)
    return profile
