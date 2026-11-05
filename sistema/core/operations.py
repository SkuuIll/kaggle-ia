"""Conservative runtime policies and useful diagnostics without GPU generation."""
PROFILES={'rapido':{'label':'Respuesta rápida','context':16384,'output':1024},'codigo':{'label':'Código','context':32768,'output':4096},'contexto':{'label':'Contexto largo','context':131072,'output':8192}}
PHASES={'assigned':'GPU asignada','install':'Instalando servidor','download':'Descargando pesos','register':'Registrando modelo','warm':'Cargando en GPU','ready':'Listo','stopped':'Finalizando procesos; esperando confirmación de Kaggle','failed':'Error en el arranque'}
def limits(started,idle,active,now,idle_minutes,maximum):
 return {'idle_remaining':max(0,int(idle_minutes*60-(now-idle))) if not active else None,'session_remaining':max(0,int(maximum*60-(now-started)))}
def diagnostic(state,status,resident):
 if state in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED','MISSING','NOT_CONFIGURED'):return 'La IA está apagada. Encendela y esperá LISTO.'
 if state=='QUEUED':return 'Kaggle está en cola; todavía no hay una IA disponible.'
 if status==401:return 'La clave HTTPS no coincide. Volvé a preparar la configuración privada.'
 if status!=200:return 'El canal de inferencia no responde; puede estar instalando o descargando. Revisá Actividad.'
 if not resident:return 'La API responde, pero el modelo no está cargado en GPU.'
 return 'API y modelo cargado disponibles. Si Paseo falla, revisá su daemon y el proveedor seleccionado.'


def failure_detail(error):
 if isinstance(error,TimeoutError) or 'Timeout' in type(error).__name__:return 'Tiempo de espera agotado. Revisá el estado antes de repetir la acción.'
 if isinstance(error,ConnectionError) or 'Connection' in type(error).__name__:return 'Conexión no disponible. Ejecutá el diagnóstico de la cuenta.'
 if isinstance(error,ValueError):return 'La configuración o el estado actual no permite esta acción. Revisá el resultado en Actividad.'
 return 'No se confirmó la operación. Revisá Actividad y la sesión real en Kaggle antes de reintentar.'


def apply_profile(profile,preset):
 import re
 data=PROFILES[preset]
 profile.update(context=data['context'],output_tokens=data['output'],performance_profile=preset)
 profile['label']=re.sub(r' - \d+k(?= |$)',f" - {data['context']//1024}k",profile['label'])
 return profile
