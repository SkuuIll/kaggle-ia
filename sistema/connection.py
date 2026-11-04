"""Private relay settings are imported separately from program files."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
def settings():
    path=BASE/'.private/connection.json'
    if not path.exists():raise RuntimeError('Falta la conexion privada. Importa tu respaldo desde MENU_IA.')
    data=json.loads(path.read_text(encoding='utf8'))
    for name in ('host','user'):
        value=data.get(name,'')
        if not isinstance(value,str) or not value or value.startswith('-') or any(c.isspace() for c in value) or '@' in value:
            raise ValueError('Configuracion SSH invalida: '+name)
    data['port']=int(data.get('port',22))
    if not 1<=data['port']<=65535:raise ValueError('Puerto SSH invalido')
    return data
