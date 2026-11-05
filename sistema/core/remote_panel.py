"""Connect the Windows clients to measured, loopback-only VPS proxy ports."""
import json,subprocess,sys,os,time,socket,webbrowser
from pathlib import Path
BASE=Path(__file__).resolve().parent
if BASE.name in ('chat','pool','accounts','clients','core','templates','web','tests'):BASE=BASE.parent

def listening(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=1):return True
    except OSError:return False

def command(config):
    args=['ssh','-N','-T','-i',str(BASE/'.private/kaggle_relay'),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','UserKnownHostsFile='+str(BASE/'.private/known_hosts'),'-o','StrictHostKeyChecking=yes','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-o','ConnectTimeout=10']
    for port in (19000, 19134, 19860, 19861, 19862, 19863, 19864, 19865, 19866):args+=['-L',f'127.0.0.1:{port}:127.0.0.1:{port}']
    return args+['-p',str(config.get('port',22)),config['user']+'@'+config['host']]

def ensure_remote(open_browser=False):
    config=json.loads((BASE/'.private/panel-remote.json').read_text())
    if not (BASE/'.private/api-clients.json').exists() and not all(listening(p) for p in (19134,19860)):
        log=open(BASE/'.private/remote-panel.log','a')
        python=Path(sys.executable);hidden=python.with_name('pythonw.exe')
        subprocess.Popen([str(hidden if hidden.exists() else python),str(Path(__file__)),'supervise'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for _ in range(100):
            if all(listening(p) for p in (19134,19860)):break
            time.sleep(.1)
        else:raise RuntimeError('No se pudo conectar el relay de la VPS. Revisa SSH y los puertos locales.')
    if open_browser:webbrowser.open(config['url'])
    return config['url']

if __name__=='__main__':
    if 'supervise' in sys.argv:
        config=json.loads((BASE/'.private/panel-remote.json').read_text())
        while True:
            if any(listening(p) for p in (19134,19860)):time.sleep(3);continue
            subprocess.run(command(config),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));time.sleep(3)
    else:print(ensure_remote(open_browser=True))
