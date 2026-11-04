"""Sequential, loopback-only visual helper for future Kaggle sessions."""
VISION_MODEL='huihui_ai/qwen2.5-vl-abliterated:3b-instruct-q4_K_M'
VISION_DIGEST='sha256:67f505b225fb4e9186e89a349659fd935520f7771b44fadbae340d7860c3987c'

def analyze_visual(coder,images,prompt,client):
    import base64
    if not isinstance(images,list) or not 1<=len(images)<=8:raise ValueError('Enviá de una a ocho imágenes o fotogramas.')
    cleaned=[]
    for image in images:
        if not isinstance(image,str) or not image.startswith('data:image/') or ';base64,' not in image:raise ValueError('Formato visual no admitido.')
        encoded=image.split(';base64,',1)[1]
        if len(encoded)>20*1024*1024:raise ValueError('Imagen demasiado grande.')
        base64.b64decode(encoded,validate=True);cleaned.append(encoded)
    def post(path,payload,timeout=600):
        response=client.post('http://127.0.0.1:11434'+path,json=payload,timeout=timeout);response.raise_for_status();return response.json()
    # The gateway serializes normal inference with this operation.
    post('/api/generate',{'model':coder,'keep_alive':0})
    try:
        tags=client.get('http://127.0.0.1:11434/api/tags',timeout=15);tags.raise_for_status()
        existing=next((m for m in tags.json().get('models',[]) if m.get('name')==VISION_MODEL),None)
        if not existing:
            post('/api/pull',{'model':VISION_MODEL,'stream':False})
            tags=client.get('http://127.0.0.1:11434/api/tags',timeout=15);tags.raise_for_status()
            existing=next((m for m in tags.json().get('models',[]) if m.get('name')==VISION_MODEL),None)
        digest=(existing or {}).get('digest','')
        if digest.removeprefix('sha256:')!=VISION_DIGEST.removeprefix('sha256:'):raise ValueError('La revisión de visión no coincide con el manifiesto fijado. No se interpretaron imágenes.')
        result=post('/api/chat',{'model':VISION_MODEL,'messages':[{'role':'user','content':str(prompt)[:8000],'images':cleaned}],'stream':False,'keep_alive':0,'options':{'num_ctx':8192,'num_predict':512,'temperature':0.1}})
        text=result.get('message',{}).get('content','')
        if not text:raise ValueError('El auxiliar de visión no devolvió una observación.')
        return {'text':text,'model':VISION_MODEL,'digest':VISION_DIGEST,'notice':'Observación auxiliar de las imágenes o muestras de video enviadas; no representa todo el video ni su audio.'}
    finally:
        post('/api/generate',{'model':VISION_MODEL,'keep_alive':0},timeout=30)


def observe_frames(backend,images,prompt,post,cancel=None):
    if not images or len(images)>8:raise ValueError('Cantidad de imágenes no permitida.')
    observations=[];seen={}
    for index,image in enumerate(images,1):
        if cancel is not None and cancel.is_set():raise InterruptedError('Análisis cancelado.')
        instruction='Describí únicamente esta imagen: formas, colores y texto visible. No deduzcas una secuencia temporal a partir de esta imagen aislada. Consulta del usuario: '+str(prompt)[:8000]
        if image not in seen:
            response=post(f'http://127.0.0.1:{backend}/control/vision',json={'images':[image],'prompt':instruction},timeout=(10,650))
            response.raise_for_status();seen[image]=response.json()['text']
        text=seen[image]
        observations.append(('Imagen/fotograma '+str(index)+' en el orden de entrada: '+text) if len(images)>1 else text)
    return '\n\n'.join(observations)
