"""Start the local panel/proxy service without starting any GPU."""
import os,subprocess,sys,time,webbrowser
from pathlib import Path
import requests
BASE=Path(__file__).resolve().parent
URL='http://127.0.0.1:8765'
def ensure_panel(open_browser=False):
    if (BASE/'.private/panel-remote.json').exists():
        from remote_panel import ensure_remote
        return ensure_remote(open_browser)
    def alive():
        try:return requests.get(URL+'/health',timeout=1).json().get('service')=='kaggle-ia-panel'
        except (requests.RequestException,ValueError):return False
    if not alive():
        folder=BASE/'.private';folder.mkdir(exist_ok=True)
        python=Path(sys.executable);pythonw=python.with_name('pythonw.exe')
        executable=pythonw if pythonw.exists() else python
        log=open(folder/'panel.log','a',encoding='utf8')
        subprocess.Popen([str(executable),str(BASE/'panel_server.py')],cwd=BASE,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for _ in range(100):
            if alive():break
            time.sleep(.1)
        else:raise RuntimeError('No se pudo iniciar el panel. Revisa si los puertos8765,19134 o19860 estan ocupados.')
    if open_browser:webbrowser.open(URL)
    return URL
if __name__=='__main__':print(ensure_panel(open_browser='--open' in sys.argv))
