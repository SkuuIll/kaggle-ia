"""Prepare a selected model and update clients only after successful inference."""
import json
import shutil
import sys,os
import time
from pathlib import Path

import requests
import yaml

BASE=Path(__file__).resolve().parent
if BASE.name in ('chat','pool','accounts','clients','core','templates','web','tests'):BASE=BASE.parent
CATALOG=BASE/'model_profiles.json'
URL='http://127.0.0.1:18134'


def catalog():
    if not CATALOG.exists():
        example=BASE/'model_profiles.example.json'
        if not example.exists():raise RuntimeError('Falta el catalogo de ejemplo de la instalacion.')
        shutil.copy2(example,CATALOG)
    return json.loads(CATALOG.read_text(encoding='utf8'))


def prepare(key=None):
    data=catalog()
    key=key or data['selected']
    p=data['profiles'][key]
    name=p['model']
    URL='http://127.0.0.1:'+str(p.get('port',18134))
    if p.get('engine') not in ('exl3','llama') and p['source']:
        exists=requests.post(URL+'/api/show',json={'model':p['source']},timeout=15)
        if not exists.ok:
            print('Descargando el modelo en Kaggle; la primera vez puede tardar varios minutos.',flush=True)
            last=0
            with requests.post(URL+'/api/pull',json={'model':p['source'],'stream':True},stream=True,timeout=(10,900)) as r:
                r.raise_for_status()
                for line in r.iter_lines(chunk_size=1):
                    if not line: continue
                    item=json.loads(line)
                    if item.get('error'): raise RuntimeError(item['error'])
                    if time.monotonic()-last>5 or item.get('status')=='success':
                        total=item.get('total',0);done=item.get('completed',0)
                        print(f"{item.get('status')}: {done/1e9:.2f}/{total/1e9:.2f} GB" if total else item.get('status'),flush=True)
                        last=time.monotonic()
        parameters={'num_ctx':p['context'],'num_gpu':99,'temperature':p['temperature'],**p.get('parameters',{})}
        r=requests.post(URL+'/api/create',json={'model':name,'from':p['source'],
                        'parameters':parameters,'stream':False},timeout=120)
        r.raise_for_status()
    print('Comprobando generacion: '+p['label']+'...',flush=True)
    if p.get('engine') in ('exl3','llama'):
        r=requests.post(URL+'/v1/chat/completions',json={'model':name,'messages':[{'role':'user','content':'Responde solamente MODELO_LISTO'}],
                        'reasoning_effort':'none','max_tokens':64},timeout=(10,600))
        r.raise_for_status()
        if not r.json()['choices'][0]['message'].get('content'):
            raise RuntimeError('El motor no devolvió texto visible.')
        return key,p
    body={'model':name,'messages':[{'role':'user','content':'Responde solamente MODELO_LISTO'}],
          'stream':False,'keep_alive':-1,'options':{'num_predict':256}}
    if p['reasoning']: body['think']=False if p.get('effort')=='none' else p.get('effort',True)
    r=requests.post(URL+'/api/chat',json=body,timeout=(10,600));r.raise_for_status()
    response=r.json()
    if response.get('error') or not response.get('message',{}).get('content'):
        raise RuntimeError('El modelo no confirmo una respuesta de texto; configuracion anterior conservada.')
    return key,p


def client_connection(model):
    path=BASE/'.private/api-clients.json'
    if path.exists():
        acc='pool' if model.get('is_pool') or str(model.get('account'))=='pool' else str(model['account'])
        data=json.loads(path.read_text(encoding='utf8'))
        if acc in data:return data[acc]['url'],data[acc]['token']
    if model.get('is_pool') or str(model.get('account'))=='pool':
        return 'https://ia.example.com/inference/pool/v1','none'
    return 'http://127.0.0.1:'+str(model.get('client_port',19860))+'/v1','none'

def sync_clients(key):
    if os.environ.get('IA_SERVER_MODE')=='vps':
        data=catalog();data['selected']=key;CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');return
    data=catalog();p=data['profiles'][key]
    choices=[p]+[v for k,v in data['profiles'].items() if k!=key and v.get('enabled',True)]
    for model in data['profiles'].values():model['client_port']=19134 if model['account']==1 else 19860
    def backup(path,label):
        folder=BASE/'.private/client-config-backup';folder.mkdir(parents=True,exist_ok=True)
        target=folder/(label+path.suffix)
        if path.exists() and not target.exists():shutil.copy2(path,target)
    path=Path.home()/'.continue/config.yaml';backup(path,'continue-profile')
    config=yaml.safe_load(path.read_text(encoding='utf8')) if path.exists() else {'name':'Kaggle SSH','version':'1.0.0','schema':'v1'}
    managed={v['model'] for v in data['profiles'].values()}
    others=[m for m in config.get('models',[]) if m.get('model') not in managed and not any('127.0.0.1:'+str(port) in m.get('apiBase','') for port in (18134,17860,19134,19860))]
    pool_url,pool_token=client_connection({'is_pool':True})
    pool_cont={'name':'Pool 24/7: Qwen 3.8 27B (Rotación Continua)','provider':'openai','model':'qwen-3.8-27b','apiBase':pool_url,'apiKey':pool_token,
               'roles':['chat','edit','apply'],'capabilities':['tool_use'],'defaultCompletionOptions':{'contextLength':p['context'],'maxTokens':p.get('output_tokens',8192),'temperature':p['temperature']},
               'requestOptions':{'extraBodyProperties':{'reasoning_effort':p.get('effort','medium')}}}
    entries=[pool_cont]
    for model in choices:
        entry={'name':f"Cuenta {model['account']}: "+model['label'],'provider':'openai','model':model['model'],'apiBase':client_connection(model)[0],'apiKey':client_connection(model)[1],
               'roles':['chat','edit','apply'],'capabilities':['tool_use'],'defaultCompletionOptions':{'contextLength':model['context'],'maxTokens':model.get('output_tokens',4096),'temperature':model['temperature']}}
        if model.get('effort'):entry['requestOptions']={'extraBodyProperties':{'reasoning_effort':model['effort']}}
        entries.append(entry)
    config['models']=entries+others
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False),encoding='utf8')
    path=Path.home()/'.config/opencode/opencode.json';backup(path,'opencode-profile')
    config=json.loads(path.read_text(encoding='utf8')) if path.exists() else {'$schema':'https://opencode.ai/config.json','provider':{},'compaction':{'auto':True,'prune':True,'reserved':8192}}
    disabled={v['provider_id'] for v in data['profiles'].values() if not v.get('enabled',True)}
    for provider_id in disabled:config.setdefault('provider',{}).pop(provider_id,None)
    variants={
        'none':{'reasoning':False,'options':{'reasoningEffort':'none'}},
        'low':{'reasoning':True,'options':{'reasoningEffort':'low'}},
        'medium':{'reasoning':True,'options':{'reasoningEffort':'medium'}},
        'high':{'reasoning':True,'options':{'reasoningEffort':'high'}}
    }
    for model in choices:
        item={'name':f"Cuenta {model['account']}: "+model['label'],'reasoning':model['reasoning'],'tool_call':True,'limit':{'context':model['context'],'output':model.get('output_tokens',4096)},'cost':{'input':0,'output':0},'variants':variants}
        if model.get('effort'):item['options']={'reasoningEffort':model['effort']}
        config.setdefault('provider',{})[model['provider_id']]={'npm':'@ai-sdk/openai-compatible','name':model['provider_label'],
            'options':{'baseURL':client_connection(model)[0],'apiKey':client_connection(model)[1],'timeout':600000,'headerTimeout':600000,'chunkTimeout':600000},
            'models':{model['model']:item}}
    pool_oc_model={'name':'Pool 24/7: Qwen 3.8 27B','reasoning':p.get('reasoning',True),'tool_call':True,'limit':{'context':p['context'],'output':p.get('output_tokens',8192)},'cost':{'input':0,'output':0},'variants':variants,'options':{'reasoningEffort':p.get('effort','medium')}}
    config.setdefault('provider',{})['pool']={'npm':'@ai-sdk/openai-compatible','name':'Pool 24/7 (Rotación Continua)',
        'options':{'baseURL':pool_url,'apiKey':pool_token,'timeout':600000,'headerTimeout':600000,'chunkTimeout':600000},
        'models':{'qwen-3.8-27b':pool_oc_model}}
    config['enabled_providers']=list(dict.fromkeys(['pool']+[v for v in config.get('enabled_providers',[]) if v not in disabled]+[v['provider_id'] for v in choices]))
    config['model']=p['provider_id']+'/'+p['model'];config['small_model']=config['model']
    for mode in ('build','plan'):config.setdefault('agent',{}).setdefault(mode,{})['temperature']=p['temperature']
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
    path=Path.home()/'.paseo/config.json';backup(path,'paseo-profile')
    config=json.loads(path.read_text(encoding='utf8')) if path.exists() else {'version':1,'daemon':{'listen':'127.0.0.1:6767','cors':{'allowedOrigins':['https://app.paseo.sh']},'relay':{'enabled':False}},'app':{'baseUrl':'https://app.paseo.sh'},'agents':{'providers':{}}}
    daemon_cfg=config.setdefault('daemon',{'listen':'127.0.0.1:6767','relay':{'enabled':False}})
    daemon_cfg.setdefault('listen','127.0.0.1:6767')
    daemon_cfg.setdefault('cors',{'allowedOrigins':['https://app.paseo.sh']})
    config.setdefault('app',{'baseUrl':'https://app.paseo.sh'})
    providers=config.setdefault('agents',{}).setdefault('providers',{})
    for model in data['profiles'].values():
        if not model.get('enabled',True):providers.pop(model['paseo_provider'],None)
    template=providers.get('qwen-kaggle',{'extends':'opencode'})
    local_programs=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'Programs'
    thinking_options=[
        {'id':'none','label':'Directo (sin pensar)'},
        {'id':'low','label':'Pensamiento breve'},
        {'id':'medium','label':'Pensamiento medio','isDefault':True},
        {'id':'high','label':'Pensamiento profundo'}
    ]
    for model in choices:
        entry={**template,'env':dict(template.get('env',{}))}
        entry['command']=[str(local_programs/'OpenCode/opencode.exe')]
        entry['env']['OPENCODE_CONFIG']=str(Path.home()/'.config/opencode/opencode.json')
        entry['label']=model['provider_label']
        entry['models']=[{'id':model['provider_id']+'/'+model['model'],'label':f"Cuenta {model['account']}: "+model['label'],'isDefault':True,'thinkingOptions':thinking_options}]
        providers[model['paseo_provider']]=entry
    if 'qwen-kaggle' not in providers:providers['qwen-kaggle']=dict(providers[choices[0]['paseo_provider']])
    providers['qwen-kaggle']['label']='IA Kaggle'
    for provider_id in {m['paseo_provider'] for m in choices}|{'qwen-kaggle'}:
        providers[provider_id]['models']=[{'id':m['provider_id']+'/'+m['model'],'label':f"Cuenta {m['account']}: "+m['label'],'isDefault':i==0,'thinkingOptions':thinking_options} for i,m in enumerate(choices)]
    if len(choices) > 1:
        pool_entry = dict(providers['qwen-kaggle'])
        pool_entry['label'] = 'IA Kaggle (Pool 24/7)'
        pool_entry['models'] = [{'id':'pool/qwen-3.8-27b','label':'Pool 24/7: Qwen 3.8 27B (Rotación Continua)','isDefault':True,'thinkingOptions':thinking_options}]
        providers['qwen-pool'] = pool_entry
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
    data['selected']=key;CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print('Configurado: '+p['label']+'. Abri un chat nuevo con ese proveedor.',flush=True)


if __name__=='__main__':
    try:
        data=catalog()
        key=sys.argv[1] if len(sys.argv)>1 else None
        if key is None:
            keys=list(data['profiles'])
            for i,k in enumerate(keys,1):print(f"{i}. {data['profiles'][k]['label']}")
            key=keys[int(input('Elegir modelo: '))-1]
        key,_=prepare(key)
        from panel_client import ensure_panel
        ensure_panel()
        sync_clients(key)
    except Exception as error:
        print('ERROR:',error,flush=True);sys.exit(1)
