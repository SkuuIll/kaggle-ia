"""Private, ready-to-copy client examples. Never expose them in public state."""
import json
import yaml

CLIENT_LAUNCHERS={
    'INSTALAR.bat':'@echo off\r\nchcp 65001 >nul\r\ntitle INSTALAR CLIENTES KAGGLE IA\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0sistema\\instalar.ps1" %*\r\nif errorlevel 1 echo No se completo la instalacion. Revisa el error anterior.\r\npause\r\n',
    'CONFIGURAR_CLIENTES.bat':'@echo off\r\ncall "%~dp0sistema\\python_ia.bat" "%~dp0sistema\\configure_clients.py"\r\npause\r\n',
    'ABRIR_PASEO.bat':'@echo off\r\ncall "%~dp0sistema\\python_ia.bat" "%~dp0sistema\\configure_clients.py" --open-paseo\r\nif errorlevel 1 pause\r\n',
    'sistema/python_ia.bat':'@echo off\r\nset PYTHONUTF8=1\r\nif not exist "%~dp0.venv\\Scripts\\python.exe" goto global_python\r\n"%~dp0.venv\\Scripts\\python.exe" %*\r\nexit /b %errorlevel%\r\n:global_python\r\npython %*\r\nexit /b %errorlevel%\r\n',
}

def build_configs(profile,connection):
    p=profile;model_id=p['provider_id']+'/'+p['model']
    model={'name':p['label'],'reasoning':p.get('reasoning',True),'tool_call':True,'limit':{'context':p['context'],'output':p.get('output_tokens',4096)},'options':{'reasoningEffort':p.get('effort','none')}}
    opencode={'$schema':'https://opencode.ai/config.json','provider':{p['provider_id']:{'npm':'@ai-sdk/openai-compatible','name':p['label'],'options':{'baseURL':connection['url'],'apiKey':connection['token'],'timeout':600000,'headerTimeout':600000,'chunkTimeout':600000},'models':{p['model']:model}}},'enabled_providers':[p['provider_id']],'model':model_id,'small_model':model_id,'compaction':{'auto':True,'prune':True,'reserved':8192}}
    cont={'name':'Kaggle HTTPS','version':'1.0.0','schema':'v1','models':[{'name':p['label'],'provider':'openai','model':p['model'],'apiBase':connection['url'],'apiKey':connection['token'],'roles':['chat','edit','apply'],'capabilities':['tool_use'],'defaultCompletionOptions':{'contextLength':p['context'],'maxTokens':p.get('output_tokens',4096),'temperature':p['temperature']},'requestOptions':{'extraBodyProperties':{'reasoning_effort':p.get('effort','none')}}}]}
    paseo={'version':1,'daemon':{'listen':'127.0.0.1:6767','cors':{'allowedOrigins':['https://app.paseo.sh']},'relay':{'enabled':False}},'app':{'baseUrl':'https://app.paseo.sh'},'agents':{'providers':{p['paseo_provider']:{'extends':'opencode','label':p['label'],'command':['opencode'],'models':[{'id':model_id,'label':p['label'],'isDefault':True}]}}}}
    return {'opencode':json.dumps(opencode,ensure_ascii=False,indent=2),'continue':yaml.safe_dump(cont,allow_unicode=True,sort_keys=False),'paseo':json.dumps(paseo,ensure_ascii=False,indent=2)}
