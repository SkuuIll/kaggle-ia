"""Control de cada servidor de codigo mediante Kaggle y SSH privado."""
import json,os,sys,time,subprocess,requests
from pathlib import Path
BASE=Path(__file__).resolve().parent
if BASE.name in ('chat','pool','accounts','clients','core','templates','web','tests'):BASE=BASE.parent

def check_cancel():
    flag=os.environ.get('IA_CANCEL_FILE')
    if flag and Path(flag).exists():raise RuntimeError('Inicio cancelado; se comprobara la parada por separado.')

def api(profile=None):
    account=(profile or {}).get('account',1)
    credentials=json.loads((BASE/f'kaggle({account}).json').read_text())
    if profile and profile['kernel_ref'].split('/')[0]!=credentials['username']:
        raise RuntimeError('El usuario del token no coincide con esta configuracion. Importa tu conexion privada o revisa la cuenta.')
    for name in ('KAGGLE_KEY','KAGGLE_API_TOKEN','KAGGLE_USERNAME'):os.environ.pop(name,None)
    os.environ['KAGGLE_USERNAME']=credentials['username']
    if credentials.get('api_token'):os.environ['KAGGLE_API_TOKEN']=credentials['api_token']
    else:os.environ['KAGGLE_KEY']=credentials['key']
    from kaggle.api.kaggle_api_extended import KaggleApi
    result=KaggleApi();result.authenticate();return result

def owned_contains(api,ref):
    seen=set()
    for page in range(1,101):
        batch=api.kernels_list(mine=True,page_size=100,page=page)
        refs={str(k.ref) for k in batch}
        if ref in refs:return True
        if len(batch)<100:return False
        if refs.issubset(seen):raise RuntimeError('No se pudo corroborar la paginacion de Kaggle.')
        seen.update(refs)
    raise RuntimeError('No se completo la lista de notebooks; no se puede confirmar ausencia.')

def state(api,ref):
    try:return str(api.kernels_status(ref).status).upper().split('.')[-1]
    except ValueError as error:
        if 'kernels.get' not in str(error):raise
        if not owned_contains(api,ref):return 'MISSING'
        raise
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code==404 and not owned_contains(api,ref):return 'MISSING'
        raise

def probe_state(key):
    from model_profiles import catalog
    profile=catalog()['profiles'][key]
    if not (BASE/f'kaggle({profile["account"]}).json').exists():return 'MISSING'
    result=subprocess.run([sys.executable,str(Path(__file__)),'state',key],capture_output=True,text=True)
    value=result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ''
    if result.returncode or value not in {'RUNNING','QUEUED','COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'}:
        raise RuntimeError('No se pudo confirmar el estado de la cuenta '+str(profile['account'])+'. Revisa sus credenciales.')
    return value

def require_no_other_active(key,profiles,probe=probe_state):
    for other in profiles:
        if other!=key and probe(other) in {'RUNNING','QUEUED'}:
            raise RuntimeError('Otra cuenta sigue activa ('+other+'). Usa MENU_IA para cambiar o APAGAR_TODO antes de iniciar otra.')
def main():
    from model_profiles import catalog,prepare,sync_clients
    from relay_client import ensure_relay,request_stop
    command=sys.argv[1] if len(sys.argv)>1 else 'start'
    key=sys.argv[2] if len(sys.argv)>2 else 'rapido'
    profile=catalog()['profiles'][key]
    client=api(profile);ref=profile['kernel_ref'];url='http://127.0.0.1:'+str(profile['port'])
    current=state(client,ref)
    if command=='state':print(current,flush=True);return
    if command=='snapshot':
        from usage import quota_values
        snapshot={'state':current,'quota':None,'quota_error':None,'checked_at':time.time()}
        try:
            with client.build_kaggle_client() as kaggle:snapshot['quota']=quota_values(kaggle.kernels.kernels_api_client.get_accelerator_quota_statistics())
        except Exception as error:snapshot['quota_error']='No se pudo consultar la cuota oficial: '+type(error).__name__
        print(json.dumps(snapshot),flush=True);return
    if command=='stop':
        if current in {'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING'}:
            print('No hay una ejecucion activa de este modelo. Kaggle:',current);return
        request_stop(url+'/control/stop',ref,profile['relay_role'])
        print('Parada solicitada. Esperando confirmacion de Kaggle...',flush=True)
        for _ in range(60):
            current=state(client,ref)
            if current in {'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}:
                print('Kaggle confirma la finalizacion:',current);return
            time.sleep(5)
        raise TimeoutError('No se confirmo fin de sesion; revise Active Events.')
    ensure_relay(profile['relay_role'])
    if command=='start' and current not in {'RUNNING','QUEUED'}:
        require_no_other_active(key,catalog()['profiles'])
        replace=current=='MISSING' and bool(profile.get('previous_kernel_ref'))
        if replace:
            previous=state(client,profile['previous_kernel_ref'])
            if previous in {'RUNNING','QUEUED'}:raise RuntimeError('El servidor anterior sigue activo. Detenelo desde Kaggle antes de reemplazarlo.')
        args=[sys.executable,str(BASE/'build_single_notebook.py'),key]
        subprocess.run(args+(['--replace-media'] if replace else []),check=True)
        check_cancel()
        result=client.kernels_push(str(BASE/profile['kernel_dir']),timeout='7200')
        if result.error:raise RuntimeError(result.error)
        print('Ejecucion enviada, version',result.version_number,flush=True)
        if replace:subprocess.run(args,check=True)
    started=time.monotonic();running_since=None
    while time.monotonic()-started<1800:
        check_cancel()
        elapsed=int(time.monotonic()-started);current=state(client,ref)
        if current=='QUEUED':progress='En cola de Kaggle; sin estimacion fiable.'
        else:
            if running_since is None:running_since=time.monotonic()
            remaining=max(0,600-int(time.monotonic()-running_since))
            progress='Esperando confirmacion real del modelo; consulta las etapas informadas en Actividad.'
        print(f'[{elapsed//60:02d}:{elapsed%60:02d}] Cuenta {profile["account"]}: {current}. {progress}',flush=True)
        try:
            response=requests.get(url+'/api/ps',timeout=3);response.raise_for_status()
            models=response.json().get('models',[])
            if any(m.get('name','').split(':')[0]==profile['model'] for m in models):
                prepare(key)
                from panel_client import ensure_panel
                if os.environ.get('IA_SERVER_MODE')!='vps':ensure_panel()
                sync_clients(key)
                display_url=(os.environ.get('IA_PUBLIC_ORIGIN','https://ia.example.com')+'/inference/cuenta'+str(profile['account'])+'/v1') if os.environ.get('IA_SERVER_MODE')=='vps' else url+'/v1'
                print('LISTO: '+profile['label']+' en '+display_url+'.',flush=True);return
        except requests.RequestException:pass
        if current in {'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}:raise RuntimeError('El notebook termino antes de estar listo. Revisar logs de Kaggle.')
        time.sleep(10)
    raise TimeoutError('No se confirmo disponibilidad en 30 minutos.')

if __name__=='__main__':
    try:main()
    except Exception as error:print('ERROR:',error,flush=True);sys.exit(1)
