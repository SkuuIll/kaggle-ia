"""Install/open a curated workstation template with existing HTTPS credentials."""
import argparse,json,os,subprocess,sys,time,zipfile
from pathlib import Path
from model_profiles import catalog
from templates import TOOLS
from tool_templates import build_tool_package
BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool',choices=[t['id'] for t in TOOLS]);parser.add_argument('--account');parser.add_argument('--open',action='store_true');parser.add_argument('--reinstall',action='store_true')
    args=parser.parse_args();config=catalog();key=args.account or config['selected']
    if key not in config['profiles']:raise SystemExit('Cuenta desconocida.')
    profile=config['profiles'][key];credentials=BASE/'.private/api-clients.json'
    if not credentials.exists():raise SystemExit('Prepara primero la conexion HTTPS desde Configuracion del panel.')
    connection=json.loads(credentials.read_text(encoding='utf8'))[str(profile['account'])]
    folder=BASE/'.private/tools'/args.tool;folder.mkdir(parents=True,exist_ok=True)
    previous=folder/'connection.json'
    if previous.exists() and json.loads(previous.read_text(encoding='utf8')).get('token')!=connection['token']:
        backup=folder/('connection-backup-'+time.strftime('%Y%m%d-%H%M%S')+'.json');backup.write_bytes(previous.read_bytes());backup.chmod(0o600)
    package=build_tool_package(args.tool,profile,connection,folder/'instalador-PRIVADO.zip')
    with zipfile.ZipFile(package) as archive:archive.extractall(folder)
    (folder/'connection.json').chmod(0o600)
    python=folder/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
    if not python.exists() or args.reinstall:subprocess.run([sys.executable,str(folder/'install_tool.py')],cwd=folder,check=True)
    subprocess.run([str(python),str(folder/'launch.py'),'--check'],cwd=folder,check=True)
    print('Herramienta preparada para la cuenta '+str(profile['account'])+'. No se inicio Kaggle.')
    if args.open:raise SystemExit(subprocess.call([str(python),str(folder/'launch.py')],cwd=folder))

if __name__=='__main__':main()
