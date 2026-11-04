"""Mantiene el cliente SSH local y recupera conexiones interrumpidas."""
import socket,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
PORTS={'text':(18134,),'coding2':(17860,)}
def listening(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=1):return True
    except OSError:return False

def ensure_relay(role):
    import os
    if os.environ.get('IA_SERVER_MODE')=='vps':return
    if all(listening(p) for p in PORTS[role]):return
    log=open(BASE/'.private'/f'local-{role}.log','a')
    subprocess.Popen([sys.executable,str(Path(__file__)),role],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

def supervise(role):
    from connection import settings
    connection=settings()
    ports=PORTS[role]
    while True:
        if any(listening(p) for p in ports):time.sleep(3);continue
        args=['ssh','-N','-T','-i',str(BASE/'.private/kaggle_relay'),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','UserKnownHostsFile='+str(BASE/'.private/known_hosts'),'-o','StrictHostKeyChecking=yes','-o','ExitOnForwardFailure=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3']
        for p in ports:args.extend(['-L',f'127.0.0.1:{p}:127.0.0.1:{p}'])
        args.extend(['-p',str(connection['port']),connection['user']+'@'+connection['host']])
        subprocess.run(args,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));time.sleep(3)
def request_stop(endpoint, kernel, role):
    import requests,webbrowser
    ensure_relay(role)
    last_error=None
    for _ in range(3):
        try:
            response=requests.post(endpoint,timeout=10)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error=exc
            time.sleep(2)
    webbrowser.open('https://www.kaggle.com/code/'+kernel)
    raise RuntimeError('Canal de parada no disponible. Si aun esta en cola o instalando, use Stop Session en Kaggle / Active Events. No se confirmo la detencion.') from last_error

if __name__=='__main__':supervise(sys.argv[1])
