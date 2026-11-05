"""Bounded CPU media extraction. Never downloads models or starts a GPU."""
import base64,importlib.util,json,math,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path

MAX_BYTES=15*1024*1024
MAX_DURATION=180
MAX_FRAMES=4
MAX_SIDE=896
TIMEOUT=30
ASR_TIMEOUT=90
FORMATS={'.mp4':'mov','.mov':'mov','.webm':'matroska','.mkv':'matroska','.avi':'avi',
         '.mp3':'mp3','.wav':'wav','.ogg':'ogg','.m4a':'mov','.flac':'flac'}

def _asr_dir():
    value=os.environ.get('IA_ASR_MODEL_DIR','')
    if not value:return None
    folder=Path(value).resolve()
    if not folder.is_dir() or not all((folder/name).is_file() for name in ('model.bin','config.json','tokenizer.json','manifest.json')):return None
    return folder

def capabilities():
    video=bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))
    audio=bool(shutil.which('ffmpeg') and shutil.which('ffprobe') and _asr_dir() and importlib.util.find_spec('faster_whisper'))
    return {'video_frames':video,'audio_transcription':audio,'max_duration_seconds':MAX_DURATION,
            'max_frames':MAX_FRAMES,'max_frame_side':MAX_SIDE,'downloads_models':False,
            'audio_timeout_seconds':ASR_TIMEOUT,'audio_model':'Whisper tiny multilingüe, CPU int8' if audio else None,
            'notice':'Video por muestras visuales; audio transcrito localmente por CPU cuando el indicador de transcripción está disponible.'}

def _input_args(path):
    fmt=FORMATS.get(path.suffix.lower())
    if not fmt:raise ValueError('Formato multimedia no admitido para análisis.')
    args=['-protocol_whitelist','file,pipe','-f',fmt]
    if fmt=='mov':args+=['-enable_drefs','0','-use_absolute_path','0']
    return args

def _run(command,timeout=TIMEOUT):
    try:
        return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=True,
                              timeout=max(0.1,timeout),creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0).stdout
    except (subprocess.SubprocessError,OSError) as exc:
        raise ValueError('No se pudo procesar el medio dentro de los límites de tiempo y formato.') from exc

def _probe(path):
    executable=shutil.which('ffprobe')
    if not executable:raise ValueError('El análisis requiere ffprobe instalado en el servidor.')
    raw=_run([executable,'-v','error',*_input_args(path),'-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)])
    try:
        info=json.loads(raw);duration=float(info['format']['duration'])
        if not math.isfinite(duration) or not 0<duration<=MAX_DURATION:raise ValueError()
    except (ValueError,KeyError,TypeError) as exc:raise ValueError('El medio debe tener una duración válida de hasta 180 segundos.') from exc
    return info,duration

ASR_SCRIPT=r'''import json,sys,wave
import numpy as np
from faster_whisper import WhisperModel
model=WhisperModel(sys.argv[1],device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
with wave.open(sys.argv[2],'rb') as source:
    if source.getnchannels()!=1 or source.getsampwidth()!=2 or source.getframerate()!=16000:raise ValueError('PCM ASR inválido')
    audio=np.frombuffer(source.readframes(source.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
segments,info=model.transcribe(audio,beam_size=1,vad_filter=True)
parts=[];length=0
for segment in segments:
    text=segment.text.strip();parts.append(text);length+=len(text)
    if length>=20000:break
print(json.dumps({'text':' '.join(parts)[:20000]},ensure_ascii=True))
'''

def prepare_media(path,kind):
    path=Path(path).resolve()
    if not path.is_file() or not 0<path.stat().st_size<=MAX_BYTES:raise ValueError('El medio está vacío o supera 15 MB.')
    if kind not in ('video','audio'):raise ValueError('Tipo multimedia no admitido.')
    started=time.monotonic();info,duration=_probe(path)
    if kind=='audio':
        if not capabilities()['audio_transcription']:
            return {'image_urls':[],'text':'','notice':'Audio guardado sin interpretar: falta configurar faster-whisper y un modelo ASR local. No se descargó ningún modelo.'}
        executable=shutil.which('ffmpeg')
        if not executable:raise ValueError('La transcripción requiere FFmpeg instalado.')
        with tempfile.TemporaryDirectory(prefix='.audio-',dir=path.parent) as folder:
            pcm=Path(folder)/'speech.wav'
            _run([executable,'-nostdin','-v','error','-threads','1',*_input_args(path),'-i',str(path),'-map','0:a:0','-vn','-sn','-dn','-t',str(MAX_DURATION),'-ac','1','-ar','16000','-c:a','pcm_s16le','-f','wav','-y',str(pcm)],min(30,ASR_TIMEOUT-(time.monotonic()-started)))
            raw=_run([sys.executable,'-c',ASR_SCRIPT,str(_asr_dir()),str(pcm)],ASR_TIMEOUT-(time.monotonic()-started))
        try:text=str(json.loads(raw)['text'])[:20000]
        except (ValueError,KeyError,TypeError) as exc:raise ValueError('La transcripción local no produjo texto válido.') from exc
        return {'image_urls':[],'text':text,'notice':'Transcripción automática local por CPU; puede contener errores.'}
    executable=shutil.which('ffmpeg')
    if not executable:raise ValueError('El análisis de video requiere ffmpeg instalado en el servidor.')
    stream=next((s for s in info.get('streams',[]) if s.get('codec_type')=='video'),None)
    if not stream or not 0<int(stream.get('width',0))*int(stream.get('height',0))<=16_000_000:
        raise ValueError('El video no tiene una pista visual válida de hasta 16 megapíxeles.')
    urls=[];timestamps=[round(duration*i/MAX_FRAMES,3) for i in range(MAX_FRAMES)]
    with tempfile.TemporaryDirectory(prefix='.frames-',dir=path.parent) as folder:
        for index,stamp in enumerate(timestamps):
            remaining=TIMEOUT-(time.monotonic()-started)
            if remaining<=0:raise ValueError('El análisis del video superó 30 segundos.')
            output=Path(folder)/f'frame-{index}.jpg'
            _run([executable,'-nostdin','-v','error','-threads','1',*_input_args(path),'-ss',str(stamp),'-i',str(path),
                  '-map','0:v:0','-an','-sn','-dn','-frames:v','1','-vf',f'scale={MAX_SIDE}:{MAX_SIDE}:force_original_aspect_ratio=decrease',
                  '-threads','1','-q:v','5','-y',str(output)],remaining)
            if not output.is_file() or not 0<output.stat().st_size<=2*1024*1024:raise ValueError('No se obtuvo un fotograma válido dentro del límite.')
            raw=output.read_bytes()
            if not raw.startswith(b'\xff\xd8'):raise ValueError('El fotograma extraído no es JPEG válido.')
            urls.append('data:image/jpeg;base64,'+base64.b64encode(raw).decode('ascii'))
    return {'image_urls':urls,'text':'',
            'notice':f'Fotogramas reales en segundos {timestamps}. El modelo debe admitir visión. No se transcribió ni interpretó el audio del video.'}
