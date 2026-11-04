"""Centro de control Windows: no expensive GPU comparisons or secret output."""
import json,os,re,subprocess,sys,time,zipfile
from pathlib import Path
import requests
from model_profiles import catalog,sync_clients,CATALOG
from portability import export_program,export_private,import_private
from model_settings import parse_repo,update_model
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent

def control(action,key):
    return subprocess.run([sys.executable,str(BASE/'text_control.py'),action,key],cwd=BASE).returncode==0

def choose():
    items=list(catalog()['profiles'].items())
    for i,(key,p) in enumerate(items,1):print(f'{i}. Cuenta {p["account"]}: {p["label"]}')
    n=input('Cuenta (Enter cancela): ').strip()
    return items[int(n)-1][0] if n and n.isdigit() and 1<=int(n)<=len(items) else None

def status():
    # Each account uses a new process so SDK authentication cannot leak across slots.
    for key in catalog()['profiles']:
        subprocess.run([sys.executable,str(Path(__file__)),'--status-one',key],cwd=BASE)
    print('La cuota restante no se estima: Kaggle es la fuente de las horas disponibles.')

def status_one(key):
    from coding_control import api,state
    p=catalog()['profiles'][key];current=state(api(p),p['kernel_ref'])
    print(f'Cuenta {p["account"]}: Kaggle {current}; modelo {p["label"]}')
    if current not in ('RUNNING','QUEUED'):return
    try:
        d=requests.get('http://127.0.0.1:'+str(p['port'])+'/control/status',timeout=3).json()
        if 'idle_seconds' in d:print(f'  En linea. Sin inferencia: {d["idle_seconds"]}s. Solicitudes activas: {d["active_requests"]}.')
        else:print('  En linea; esta sesion usa el controlador anterior sin temporizador visible.')
    except requests.RequestException:print('  Sin canal privado confirmado todavia; no equivale a GPU apagada.')

def stop_all():
    results=[control('stop',key) for key in catalog()['profiles']]
    print('LAS IA DE ESTE PROYECTO ESTAN FINALIZADAS EN KAGGLE.' if all(results) else 'NO SE CONFIRMO EL APAGADO DE TODAS. Revisa los errores y Active Events.')
    return all(results)

def open_paseo():
    exe=Path(os.environ.get('LOCALAPPDATA',''))/'Programs/Paseo/Paseo.exe'
    if not exe.exists():raise RuntimeError('Falta Paseo. Ejecuta INSTALAR.bat.')
    env=os.environ.copy();env['PATH']=str(exe.parent.parent/'OpenCode')+os.pathsep+env.get('PATH','')
    cli=exe.parent/'resources/bin/paseo.cmd'
    if cli.exists():
        command=['cmd.exe','/d','/c',str(cli)]
        r=subprocess.run(command+['ls','--json'],capture_output=True,text=True,env=env)
        try:agents=json.loads(r.stdout)
        except (ValueError,TypeError):agents=None
        active=isinstance(agents,list) and any(a.get('status') not in ('closed','completed','failed','stopped','idle') for a in agents)
        if active:
            subprocess.run(command+['reload'],env=env)
            print('Paseo tiene tareas activas: no se reinicio. Abri un chat nuevo; recarga Paseo al terminar las tareas si cambiaste contexto.')
        elif isinstance(agents,list):subprocess.run(command+['restart'],env=env)
        else:subprocess.run(command+['daemon','start','--timeout','30'],env=env)
    subprocess.Popen([str(exe)],env=env)

def connect():
    key=choose()
    if not key:return
    from coding_control import probe_state
    active=[other for other in catalog()['profiles'] if other!=key and probe_state(other) in ('RUNNING','QUEUED')]
    if active:
        print('Otra cuenta tiene una GPU activa. Para cambiar se detendra primero.')
        if input('Cambiar de cuenta y apagar la anterior? [s/N]: ').strip().lower()!='s':return
        if not all(control('stop',other) for other in active):raise RuntimeError('No se confirmo la parada de la cuenta anterior.')
    if control('start',key):open_paseo()

def change_model():
    key=choose()
    if not key:return
    repo=parse_repo(input('URL de Hugging Face o autor/modelo: '))
    r=requests.get('https://huggingface.co/api/models/'+repo,timeout=30);r.raise_for_status();info=r.json()
    files=[x['rfilename'] for x in info.get('siblings',[]) if x['rfilename'].endswith('.gguf') and not any(s in x['rfilename'].lower() for s in ('mmproj','draft','imatrix')) and not re.search(r'-\d{5}-of-\d{5}',x['rfilename'])]
    if not files:raise ValueError('No hay un GGUF unico compatible en ese repositorio. No se cambio el modelo.')
    files.sort(key=lambda s:('Q4_K_M' not in s,'Q4_K_S' not in s,s))
    for i,f in enumerate(files,1):print(f'{i}. {f}')
    choice=input('Archivo (Enter = 1): ').strip();filename=files[int(choice or '1')-1]
    existing=catalog()['profiles'][key]
    context=int(input(f'Contexto soportado por el modelo (Enter = {existing["context"]}): ') or existing['context'])
    if not 4096<=context<=1048576:raise ValueError('Contexto fuera de rango.')
    print('El cambio requiere detener la sesion actual de esta cuenta.')
    if input('Aplicar cambio y detenerla? [s/N]: ').strip().lower()!='s':return
    if not control('stop',key):raise RuntimeError('No se cambio nada: no se confirmo parada.')
    update_model(CATALOG,key,repo,filename,info['sha'],context,True)
    print('Modelo guardado. El proximo inicio descargara SOLO este GGUF en Kaggle y comprobara compatibilidad.')
    if input('Iniciar y conectar ahora? [S/n]: ').strip().lower()!='n' and control('start',key):open_paseo()

def timers():
    key=choose()
    if not key:return
    data=catalog();p=data['profiles'][key]
    idle=int(input(f'Apagar sin inferencia, minutos (actual {p.get("idle_minutes",15)}): ') or p.get('idle_minutes',15))
    maximum=int(input(f'Limite de sesion, minutos (actual {p.get("max_session_minutes",120)}): ') or p.get('max_session_minutes',120))
    if not 1<=idle<=120 or not 5<=maximum<=120:raise ValueError('Inactividad:1-120; sesion:5-120 minutos.')
    p.update(idle_minutes=idle,max_session_minutes=maximum);CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print('Guardado. Se aplica en el PROXIMO inicio, no a una GPU que ya esta encendida.')

def packages(private=False):
    folder=ROOT/'exportaciones';stamp=time.strftime('%Y%m%d-%H%M%S')
    if private:
        print('Este ZIP contiene tokens y clave SSH. Guardalo de forma privada; no lo subas a GitHub ni lo compartas.')
        if input('Crear respaldo PRIVADO? [s/N]: ').lower().strip()!='s':return
        out=export_private(ROOT,folder/f'conexion-PRIVADA-{stamp}.zip')
    else:out=export_program(ROOT,folder/f'instalador-ia-{stamp}.zip')
    print('Creado:',out)

def restore():
    source=Path(input('Ruta del ZIP PRIVADO (sin mostrar sus claves): ').strip().strip('"'))
    if input('Importar y reemplazar la conexion local? [s/N]: ').strip().lower()!='s':return
    import_private(ROOT,source)
    if os.name=='nt':
        import getpass
        key=BASE/'.private/kaggle_relay'
        if key.exists():
            r=subprocess.run(['icacls',str(key),'/inheritance:r','/grant:r',getpass.getuser()+':F'],capture_output=True)
            if r.returncode:print('Revisa los permisos del archivo de clave SSH antes de conectar.')
    sync_clients(catalog()['selected']);print('Conexion importada. No se inicio ninguna GPU.')

def main():
    if len(sys.argv)>1:
        if sys.argv[1]=='--status-one':status_one(sys.argv[2]);return
        if sys.argv[1]=='--status':status();return
        if sys.argv[1]=='--stop-all':sys.exit(0 if stop_all() else 1)
        if sys.argv[1]=='--export-program':print(export_program(ROOT,Path(sys.argv[2])));return
    actions={'1':status,'2':connect,'3':lambda:control('stop',key) if (key:=choose()) else None,
             '4':stop_all,'5':change_model,'6':timers,'7':packages,'8':lambda:packages(True),'9':restore}
    while True:
        print('\nCENTRO DE CONTROL IA\n1 Estado real / conexiones\n2 Iniciar y conectar Paseo + Continue\n3 Apagar una cuenta\n4 APAGAR TODAS LAS GPUs\n5 Cambiar modelo GGUF\n6 Autoapagado para proximos inicios\n7 Exportar instalador SIN claves\n8 Crear respaldo PRIVADO de conexion\n9 Importar conexion en esta PC\n0 Salir (no apaga GPUs)')
        option=input('Elegir: ').strip()
        if option=='0':print('Si hay una GPU activa, usa la opcion 4 o el panel web para detenerla.');return
        try:
            if option in actions:actions[option]()
            else:print('Opcion invalida.')
        except (Exception,KeyboardInterrupt) as error:print('No se completo la operacion:',type(error).__name__,str(error)[:300])

if __name__=='__main__':main()
