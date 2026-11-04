"""Compatibilidad con los accesos de encendido y apagado existentes."""
import sys
from coding_control import main,api
if __name__=='__main__':
    try:main()
    except Exception as error:print('ERROR:',error,flush=True);sys.exit(1)
