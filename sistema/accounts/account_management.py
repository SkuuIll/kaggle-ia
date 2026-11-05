"""Recoverable removal of panel credentials, only after a fresh terminal state."""
import time,uuid
from pathlib import Path
TERMINAL={'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'}

def remove_account(config,key,base,probe):
    base=Path(base).resolve();profile=config['profiles'][key]
    credential=base/f'kaggle({profile["account"]}).json'
    if not credential.exists():raise ValueError('Esta conexion no tiene una cuenta guardada.')
    if probe(key) not in TERMINAL:raise ValueError('No se confirmo el apagado. La cuenta se conserva para que puedas detenerla.')
    folder=base/'.private/removed-accounts';folder.mkdir(parents=True,exist_ok=True)
    archive=folder/(key+'-'+str(int(time.time()))+'-'+uuid.uuid4().hex[:8]+'.json')
    credential.replace(archive);archive.chmod(0o600)
    profile['enabled']=False
    if config.get('selected')==key:
        config['selected']=next((k for k,p in config['profiles'].items() if k!=key and (base/f'kaggle({p["account"]}).json').exists()),key)
    return archive
