"""Interactive password reset. Never accept passwords in command-line arguments."""
import getpass
from pathlib import Path
from panel_auth import PasswordGate,password_record
if __name__=='__main__':
    user=input('Usuario del panel [admin]: ').strip() or 'admin'
    password=getpass.getpass('Contrasena nueva (minimo 16 caracteres): ')
    if password!=getpass.getpass('Repetir contrasena: '):raise SystemExit('No coinciden; sin cambios.')
    path=Path(__file__).resolve().parents[1]/'.private/panel-auth.json';path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and PasswordGate(path).role(user)=='observer':raise SystemExit('Ese nombre ya pertenece a un invitado.')
    PasswordGate._save(path,password_record(user,password))
    print('Hash actualizado. Reinicia kaggle-ia para aplicar; la contrasena no se muestra.')
