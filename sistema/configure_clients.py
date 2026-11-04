"""Apply packaged client configuration locally; never starts a GPU or resets chats."""
import json,os,shutil,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent

def main():
    if '--open-paseo' in sys.argv:
        from ia_manager import open_paseo
        open_paseo();return
    from model_profiles import catalog,sync_clients
    if not (BASE/'.private/api-clients.json').exists():raise RuntimeError('Falta la configuracion privada. Descargala desde Configuracion > Conexion en el panel.')
    data=catalog();key=data.get('selected','coder2')
    backup=BASE/'.private/client-config-backup'/time.strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True,exist_ok=True)
    for label,path in [('opencode',Path.home()/'.config/opencode/opencode.json'),('paseo',Path.home()/'.paseo/config.json'),('continue',Path.home()/'.continue/config.yaml')]:
        if path.exists():shutil.copy2(path,backup/(label+path.suffix))
    sync_clients(key)
    exe=Path(os.environ.get('LOCALAPPDATA',''))/'Programs/Paseo/Paseo.exe'
    cli=exe.parent/'resources/bin/paseo.cmd'
    if cli.exists():
        import subprocess
        env=os.environ.copy();env['PATH']=str(exe.parent.parent/'OpenCode')+os.pathsep+env.get('PATH','')
        cmd=['cmd.exe','/d','/c',str(cli)]
        r=subprocess.run(cmd+['ls','--json'],capture_output=True,text=True,env=env)
        if r.returncode==0:subprocess.run(cmd+['reload'],capture_output=True,text=True,env=env)
        else:subprocess.run(cmd+['daemon','start','--timeout','15'],capture_output=True,text=True,env=env)
    print('Configuracion HTTPS aplicada a OpenCode, Paseo y Continue. Los chats existentes se conservan.')
    print('Abri ABRIR_PASEO.bat y un chat nuevo. Paseo necesita OpenCode instalado; usa INSTALAR.bat si falta.')
    print('No se inicio ni detuvo una GPU.')

if __name__=='__main__':
    try:main()
    except ImportError:print('ERROR: Faltan dependencias. Ejecuta INSTALAR.bat primero.');sys.exit(1)
    except Exception as error:print('ERROR: No se pudo aplicar la configuracion ('+type(error).__name__+'). Revisa los archivos y las copias privadas; no se muestra su contenido.');sys.exit(1)
