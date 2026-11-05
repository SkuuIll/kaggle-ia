"""Downloadable private workstation tools; no server-side pip or GPU start."""
import json,zipfile
from pathlib import Path
from templates import TOOLS

INSTALL=r'''import os,subprocess,sys,venv
from pathlib import Path
root=Path(__file__).resolve().parent
if sys.version_info[:2]!=(3,12):raise SystemExit('Usá Python 3.12 para estas herramientas.')
env=root/'.venv'
venv.EnvBuilder(with_pip=True).create(env)
python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(root/'requirements.txt')],check=True)
subprocess.run([str(python),str(root/'launch.py'),'--check'],check=True)
print('Instalación local comprobada. No se inició una GPU. Abrí ABRIR.bat cuando quieras usarla.')
'''

LAUNCH=r'''import importlib.util,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
tool=json.loads((root/'tool.json').read_text(encoding='utf8'))['id']
if '--check' in sys.argv:
    modules={'aider':['aider'],'httpx':['httpx'],'streamlit':['streamlit','httpx']}[tool]
    for name in modules:
        if importlib.util.find_spec(name) is None:raise SystemExit('Falta instalar '+name)
    print('Dependencias locales disponibles. Sin generación ni encendido de GPU.');raise SystemExit(0)
config=json.loads((root/'connection.json').read_text(encoding='utf8'))
if tool=='aider':
    project=Path(input('Ruta de tu proyecto (sin comillas): ').strip()).expanduser().resolve()
    if not project.is_dir() or project==root or root in project.parents:raise SystemExit('Elegí la carpeta de tu código, fuera del instalador privado.')
    environment={**os.environ,'OPENAI_API_BASE':config['url'],'OPENAI_API_KEY':config['token']}
    command=[sys.executable,'-m','aider','--model','openai/'+config['model'],'--no-auto-commits','--analytics-disable','--no-check-update']
    raise SystemExit(subprocess.call(command,cwd=project,env=environment))
if tool=='streamlit':
    raise SystemExit(subprocess.call([sys.executable,'-m','streamlit','run',str(root/'chat.py'),'--server.address=127.0.0.1','--server.port=8501','--browser.gatherUsageStats=false'],cwd=root))
raise SystemExit(subprocess.call([sys.executable,str(root/'client.py'),*sys.argv[1:]],cwd=root))
'''

CLIENT=r'''import argparse,json,httpx
from pathlib import Path
config=json.loads((Path(__file__).resolve().parent/'connection.json').read_text(encoding='utf8'))
def chat(messages):
    with httpx.Client(timeout=httpx.Timeout(600,connect=15)) as client:
        response=client.post(config['url']+'/chat/completions',headers={'Authorization':'Bearer '+config['token']},json={'model':config['model'],'messages':messages,'max_tokens':config.get('output_tokens',4096),'temperature':0.2,'stream':False,'reasoning_effort':'none'})
        response.raise_for_status();return response.json()['choices'][0]['message']['content']
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Cliente HTTPS de tu IA. Sin argumento consulta modelos; con --prompt genera texto.')
    parser.add_argument('--prompt');args=parser.parse_args()
    try:
        if args.prompt:print(chat([{'role':'user','content':args.prompt}]))
        else:
            with httpx.Client(timeout=15) as client:
                r=client.get(config['url']+'/models',headers={'Authorization':'Bearer '+config['token']});r.raise_for_status()
                print('Modelos disponibles:',', '.join(m['id'] for m in r.json().get('data',[])))
    except httpx.HTTPError as error:raise SystemExit('No se pudo usar la IA. Revisá Diagnóstico en el panel. HTTP: '+str(getattr(getattr(error,'response',None),'status_code','sin conexión')))
'''

CHAT=r'''import httpx,streamlit as st
from client import chat
st.set_page_config(page_title='Mi IA · Kaggle')
st.title('Mi IA de código')
st.caption('La GPU se administra desde tu panel. Esta ventana no la enciende ni la apaga. Se envían como máximo los últimos 12 mensajes; iniciá un chat nuevo para reducir contexto.')
if 'messages' not in st.session_state:st.session_state.messages=[]
if st.button('Nuevo chat'):st.session_state.messages=[];st.rerun()
for message in st.session_state.messages:
    with st.chat_message(message['role']):st.markdown(message['content'])
if prompt:=st.chat_input('Escribí tu consulta'):
    st.session_state.messages.append({'role':'user','content':prompt})
    with st.chat_message('user'):st.markdown(prompt)
    try:
        with st.chat_message('assistant'):
            with st.spinner('Consultando tu modelo…'):answer=chat(st.session_state.messages[-12:])
            st.markdown(answer)
        st.session_state.messages.append({'role':'assistant','content':answer})
    except httpx.HTTPError:st.error('La IA no respondió. Revisá el diagnóstico, la cuenta y el encendido en tu panel.')
'''

def build_tool_package(identifier,profile,connection,destination):
    tool=next((t for t in TOOLS if t['id']==identifier),None)
    if tool is None:raise ValueError('Herramienta desconocida.')
    config={'url':connection['url'],'token':connection['token'],'model':profile['model'],'output_tokens':profile.get('output_tokens',4096)}
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    instructions=f'''# {tool['name']}

Este paquete es PRIVADO: connection.json contiene la clave de inferencia. No contiene tokens Kaggle ni la clave SSH. No lo subas a GitHub.

1. Extraé el ZIP en una carpeta privada fuera de tu repositorio.
2. Con Python 3.12 instalado, ejecutá INSTALAR.bat. Se descargan las librerías oficiales a .venv, sin iniciar Kaggle.
3. Encendé el modelo desde el panel cuando lo necesites y ejecutá ABRIR.bat.

{tool['description']}

Aider solicita la carpeta de tu código; revisá sus cambios antes de aceptarlos. HTTPX consulta /models por defecto (no genera texto); para generar ejecutá `.venv\\Scripts\\python.exe client.py --prompt "Tu consulta"`. Streamlit abre un chat en http://127.0.0.1:8501; Ctrl+C termina ese chat local, no la GPU. El modelo debe estar LISTO para generar. No se mantienen conexiones artificiales para evitar el autoapagado.

Si cambiás de modelo o cuenta, descargá un paquete actualizado. Podés eliminar la carpeta para desinstalar; esto no detiene Kaggle. La instalación de dependencias no prueba la calidad de las respuestas ni el soporte de herramientas de cada modelo candidato.

Origen oficial: {tool['source']}
Versiones directas: {', '.join(tool['packages'])}. Las dependencias transitivas las resuelve pip.
'''
    bat='@echo off\r\ncd /d "%~dp0"\r\npy -3.12 install_tool.py\r\nif errorlevel 1 (echo No se completo la instalacion. Revisa Python 3.12 y tu conexion. & pause & exit /b 1)\r\npause\r\n'
    launch_bat='@echo off\r\ncd /d "%~dp0"\r\nif not exist ".venv\\Scripts\\python.exe" (echo Ejecuta primero INSTALAR.bat & pause & exit /b 1)\r\n".venv\\Scripts\\python.exe" launch.py %*\r\npause\r\n'
    files={'INSTALAR.bat':bat,'ABRIR.bat':launch_bat,'install_tool.py':INSTALL,'launch.py':LAUNCH,'requirements.txt':'\n'.join(tool['packages'])+'\n','connection.json':json.dumps(config),'tool.json':json.dumps({'id':identifier}),'README.md':instructions,'.gitignore':'*\n'}
    if identifier!='aider':files['client.py']=CLIENT
    if identifier=='streamlit':files['chat.py']=CHAT
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in files.items():archive.writestr(name,content)
    destination.chmod(0o600)
    return destination
