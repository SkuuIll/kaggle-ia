"""Interactive password reset. Never accept passwords in command-line arguments."""
import getpass,json,os
from pathlib import Path
from panel_auth import password_record
if __name__=='__main__':
    user=input('Usuario del panel [admin]: ').strip() or 'admin'
    password=getpass.getpass('Contrasena nueva (minimo 16 caracteres): ')
    if password!=getpass.getpass('Repetir contrasena: '):raise SystemExit('No coinciden; sin cambios.')
    path=_get_sys_base()/'.private/panel-auth.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(password_record(user,password)),encoding='utf8');os.chmod(path,0o600)
    print('Hash actualizado. Reinicia kaggle-ia para aplicar; la contrasena no se muestra.')
