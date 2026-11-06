"""Curated recipes: metadata only, never arbitrary remote installers."""
import copy,re

MODELS=[
 {'id':'thinkingcap-nemotron','name':'ThinkingCap Nemotron 3.5 Lightning · Abliterated','category':'MoE · llama.cpp',
  'repo':'mradermacher/ThinkingCap-Nemotron-3.5-Lightning-30B-A3B-abliterated-i1-GGUF',
  'filename':'ThinkingCap-Nemotron-3.5-Lightning-30B-A3B-abliterated.i1-IQ4_XS.gguf',
  'revision':'0085d5241dc5f1d4ed83bcd4938c03c262ccd6af','size_bytes':18718009024,'context':262144,'native_context':1048576,
  'license':'OpenMDW 1.1','engine':'llama','parameters':{},'tested':True,'effort':'none','arch':'30B MoE · 3B activos',
  'description':'Ventana de 262.144 en dos T4. Recuperó cinco datos con 249.998 tokens de entrada. Medición corta: 78,9 TPS en código y 85,1 en prosa.'},
 {'id':'qwen38-heretic-exl3','name':'Qwen3.8 27B Heretic ARA · EXL3 + DFlash2','category':'EXL3 · TabbyAPI',
  'repo':'Honkware/Qwen3.8-27B-heretic-ara-exl3-4.0bpw','filename':'model-00001-of-00003.safetensors',
  'revision':'1d09f16a35dc3c23b9634741bf61e6c746fcce21','size_bytes':8471336006,'download_bytes':17178659341,
  'context':131072,'native_context':262144,'license':'Apache-2.0','engine':'exl3','parameters':{},'tested':True,
  'arch':'27B DeltaNet + DFlash2','description':'Perfil anterior de producción. Mediana de 49,2 TPS en código corto en dos T4.'},
 {'id':'qwen38-heretic-rvn','name':'Qwen3.8 27B RVN Heretic · Multilingual MTP','category':'Modelo Único · 27B DeltaNet + MTP (128k)','repo':'0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF','filename':'RVN-Q4_K_M-multilingual-mtp.gguf','revision':'ab8d7bd81d03117501e4da60cccdff4c80f0eea0','size_bytes':16998720992,'context':131072,'native_context':262144,'license':'Apache-2.0','parameters':{'draft_num_predict':2,'num_batch':512},'tested':True,
  'arch':'27B Híbrido DeltaNet + MTP (draft=2)','tps_range':'26–36 TPS','vram_fit':'17.0 GB pesos · 15.0 GB libres (KV -75%)','speed_badge':'Único activo · ARA KL 0.0085 + MTP','tps_tier':'ultra',
  'description':'Refinado con 3 pasadas ARA (0-1% rechazos, preservación KL 0.0085), calibración multilingüe/código v5, cabezal MTP optimizado (draft_num_predict=2, +59% TPS en Q4_K_M), reasoning_effort=medium y 48 capas Gated DeltaNet (-75% caché KV en 128k).'},
]
for _model in MODELS:_model['low_restriction']=True
TOOLS=[
 {'id':'aider','name':'Aider · asistente de terminal','category':'Herramientas','source':'https://github.com/Aider-AI/aider','packages':['aider-chat==0.86.2'],'description':'Edición y revisión de proyectos desde una terminal con tu API HTTPS. Instalador aislado para Windows/Python 3.12.'},
 {'id':'httpx','name':'Cliente Python · HTTPX','category':'Herramientas','source':'https://github.com/encode/httpx','packages':['httpx==0.28.1'],'description':'Plantilla de integración HTTP con timeout, diagnóstico sin generación y ejemplo de chat con tu cuenta.'},
 {'id':'streamlit','name':'Chat web local · Streamlit','category':'Herramientas','source':'https://github.com/streamlit/streamlit','packages':['streamlit==1.66.1','httpx==0.28.1'],'description':'Chat en tu PC conectado a la IA de Kaggle. Escucha solo en localhost y genera únicamente cuando enviás un mensaje.'},
]
WORKFLOWS=[
 {'id':'web','name':'Crear una interfaz web','category':'Instrucciones','prompt':'Revisá la estructura del proyecto y sus convenciones. Implementá la interfaz que te describo: [OBJETIVO]. Usá sus librerías actuales, componentes accesibles, diseño responsive y estados de carga, vacío y error. Proponé los archivos a cambiar, implementá y verificá el flujo completo sin inventar resultados.'},
 {'id':'debug','name':'Diagnosticar y corregir errores','category':'Instrucciones','prompt':'Investigá este error: [ERROR Y PASOS]. Reproducilo o identificá evidencia verificable, seguí el flujo hasta la causa y corregí el problema. Conservá los datos del usuario. Agregá una prueba útil cuando corresponda y explicá qué validaste y qué sigue pendiente.'},
 {'id':'refactor','name':'Refactorizar con cambios controlados','category':'Instrucciones','prompt':'Mejorá [MÓDULO] conservando su comportamiento observable y las interfaces usadas por otros módulos. Primero inspeccioná dependencias y pruebas. Simplificá la lógica con cambios pequeños y comprobá compatibilidad; evitá reescrituras ajenas al objetivo.'},
 {'id':'tests','name':'Generar pruebas útiles','category':'Instrucciones','prompt':'Analizá [MÓDULO O FLUJO] y escribí pruebas de sus requisitos, errores reales y casos límite. Priorizá pruebas que detecten regresiones sobre detalles internos. Ejecutalas y reportá resultados reales, incluyendo cualquier dependencia externa que no hayas podido comprobar.'},
 {'id':'docs','name':'Documentar e instalar un proyecto','category':'Instrucciones','prompt':'Revisá el código y prepará documentación reproducible: propósito, requisitos, instalación, configuración sin exponer claves, arranque, parada, ejemplos y solución de errores. Comprobá los comandos posibles en este entorno y distinguí lo verificado de lo pendiente.'},
]
SOURCES=[
 {'name':'Qwen3-Coder & MoE A3B','url':'https://github.com/QwenLM/Qwen3-Coder','use':'Arquitectura Mixture-of-Experts (30B totales, 3.3B activos por token) ideal para maximizar TPS en Tesla T4.'},
 {'name':'Ollama (FlashAttention + KV Q8_0)','url':'https://github.com/ollama/ollama','use':'Motor con FlashAttention-2 y caché KV cuantizada a 8 bits activados en el notebook para duplicar margen de VRAM y elevar TPS.'},
 {'name':'llama.cpp & Multi-Token Prediction','url':'https://github.com/ggml-org/llama.cpp','use':'Soporte subyacente de cuantización GGUF y decodificación MTP (draft_num_predict=4) en GPUs NVIDIA Turing (sm_75).'},
 {'name':'Kaggle LLM Server','url':'https://github.com/Tahsine/kaggle-llm-server','use':'Referencia de arquitectura para aislar pesos temporales en /kaggle/temp sin saturar el disco de salida.'}
]

def get_template(identifier):
    value=next((t for t in MODELS if t['id']==identifier),None)
    if value is None:raise ValueError('Plantilla desconocida. Elegí una del catálogo.')
    return copy.deepcopy(value)

def prepare_profile(profile,identifier,metadata):
    t=get_template(identifier)
    if metadata.get('sha')!=t['revision']:raise ValueError('La revisión no coincide con la plantilla fijada.')
    file=next((f for f in metadata.get('siblings',[]) if f.get('rfilename')==t['filename']),None)
    if not file or file.get('size')!=t['size_bytes']:raise ValueError('El archivo o su tamaño no coincide con la plantilla.')
    native=metadata.get('gguf',{}).get('context_length')
    if native and t['context']>native:raise ValueError('El contexto supera el informado por el modelo.')
    result=copy.deepcopy(profile)
    result.pop('cache_source',None)
    result.pop('engine',None)
    if 'engine' in t:result['engine']=t['engine']
    result.update(repo=t['repo'],filename=t['filename'],revision=t['revision'],context=t['context'],parameters=t['parameters'],source=None,
                  label=t['name']+f" - {t['context']//1024}k (cuenta {profile['account']})",temperature=0.2,reasoning=True,effort=t.get('effort','medium'),output_tokens=8192 if t['context']>=131072 else 4096,
                  performance_profile='contexto' if t['context']>=131072 else 'codigo' if t['context']==32768 else 'rapido',template_id=t['id'])
    if result['performance_profile']=='rapido':result['output_tokens']=1024
    return result
