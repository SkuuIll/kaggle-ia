import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import base64,io,json,struct,tempfile,time,unittest, zipfile,zlib
from pathlib import Path
from unittest.mock import patch
from chat_engine import ChatStore

def _sample_png(width=4,height=3):
    sig=b'\x89PNG\r\n\x1a\n'
    ihdr=struct.pack('>IIBBBBB',width,height,8,2,0,0,0)
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    raw_rows=b''.join(b'\x00'+(b'\xff\x00\x00'*width) for _ in range(height))
    idat=zlib.compress(raw_rows)
    return sig+chunk(b'IHDR',ihdr)+chunk(b'IDAT',idat)+chunk(b'IEND',b'')

def _sample_docx(text='Documento de prueba en Word'):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('word/document.xml',f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')
    return buf.getvalue()

def _sample_pdf(text='Texto dentro del PDF'):
    stream_data=zlib.compress(f'BT /F1 12 Tf 72 712 Td ({text}) Tj ET'.encode('latin1'))
    body=(b'%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n'
          b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n'
          b'3 0 obj << /Type /Page /Parent 2 0 R /Contents 4 0 R >> endobj\n'
          b'4 0 obj << /Length '+str(len(stream_data)).encode()+b' /Filter /FlateDecode >>\nstream\n'+stream_data+b'\nendstream\nendobj\n%%EOF')
    return body

class FakeStreamResponse:
    def __init__(self,status_code=200,chunks=None):
        self.status_code=status_code
        self.ok=200<=status_code<300
        self._chunks=chunks or []
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_lines(self,chunk_size=512,decode_unicode=False):
        for c in self._chunks:
            yield c.encode('utf-8')

class ChatEngineTests(unittest.TestCase):
    def test_failed_generation_is_not_sent_as_a_prior_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp))
            history=[
                {'id':'1','role':'user','content':'Explicá este código','status':'done'},
                {'id':'2','role':'assistant','content':'No se pudo conectar','status':'error'},
                {'id':'3','role':'user','content':'Intentá otra vez','status':'done'},
            ]
            messages=store._build_api_messages({},history,{})
            self.assertEqual([m['role'] for m in messages],['system','user','user'])

    def test_document_preview_returns_extracted_text_as_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp))
            conversation=store.create_conversation('rapido')
            source='<script>text example</script>'
            attached=store.upload_attachment(conversation['id'],'example.html','text/html',
                                             base64.b64encode(source.encode()).decode())
            self.assertEqual(store.get_attachment_preview(attached['id']),{'text':source})
            with self.assertRaises(ValueError):
                store.get_attachment_preview('missing')

    def test_stream_usage_is_saved_with_the_answer_after_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp))
            cid=store.create_conversation('rapido')['id']
            response=FakeStreamResponse(200,[
                'data: {"choices":[{"delta":{"content":"Hola"}}]}',
                'data: {"choices":[],"usage":{"completion_tokens":12,"completion_tokens_per_sec":42.5}}',
                'data: [DONE]',
            ])
            with patch('chat_engine.requests.post',return_value=response) as post:
                result=store.start_send(cid,'Saludá',[],{'account':1,'model':'test'})
                for _ in range(100):
                    state=store.get_request(result['request_id'])
                    if state['status']!='running':break
                    time.sleep(.01)
                self.assertEqual(state['status'],'done')
                self.assertTrue(post.call_args.kwargs['json']['stream_options']['include_usage'])
            answer=ChatStore(Path(tmp)).get_conversation(cid)['messages'][-1]
            self.assertEqual(answer['measurement']['tokens'],12)
            self.assertEqual(answer['measurement']['tps'],42.5)
            self.assertEqual(answer['measurement']['measurement_kind'],'generation')

    def test_conversation_lifecycle_and_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp))
            created=store.create_conversation('rapido','Mi primera charla','Respondé en español.')
            self.assertEqual(created['title'],'Mi primera charla')
            self.assertEqual(len(store.list_conversations()),1)
            updated=store.update_conversation(created['id'],title='Título editado',account='coder2')
            self.assertEqual(updated['title'],'Título editado')
            self.assertEqual(updated['account'],'coder2')
            store.archive_conversation(created['id'])
            self.assertEqual(store.list_conversations(),[])

    def test_multimodal_attachments_extract_and_export_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            store=ChatStore(root)
            conv=store.create_conversation('rapido','Prueba adjuntos')
            cid=conv['id']
            img=store.upload_attachment(cid,'captura.png','image/png',base64.b64encode(_sample_png(8,6)).decode())
            self.assertEqual(img['kind'],'image')
            self.assertIn('8×6',img['summary'])
            doc=store.upload_attachment(cid,'informe.docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document',base64.b64encode(_sample_docx('Presupuesto anual aprobado')).decode())
            self.assertEqual(doc['kind'],'document')
            pdf=store.upload_attachment(cid,'manual.pdf','application/pdf',base64.b64encode(_sample_pdf('Clausula de seguridad')).decode())
            self.assertEqual(pdf['kind'],'document')
            code=store.upload_attachment(cid,'main.py','text/x-python',base64.b64encode(b'print("hola mundo")\n').decode())
            self.assertEqual(code['kind'],'code')
            # This test exercises storage/export; valid frame extraction is tested separately.
            with patch('chat_media.capabilities',return_value={'video_frames':False,'audio_transcription':False}):
                vid=store.upload_attachment(cid,'demo.mp4','video/mp4',base64.b64encode(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom').decode())
            self.assertEqual(vid['kind'],'video')

            meta,disk_path=store.get_attachment_file(img['id'])
            self.assertEqual(meta['name'],'captura.png')
            self.assertTrue(disk_path.is_file())

            with self.assertRaises(ValueError):
                store.upload_attachment(cid,'corrupta.png','image/png',base64.b64encode(b'not-an-image').decode())

            calls=[]
            def fake_post(url,json=None,**kwargs):
                calls.append(json)
                return FakeStreamResponse(200,[
                    'data: {"choices":[{"delta":{"content":"Análisis "}}]}',
                    'data: {"choices":[{"delta":{"content":"completado."}}]}',
                    'data: [DONE]'
                ])

            profile={'account':1,'model':'qwen3-coder','temperature':0.2,'output_tokens':2048}
            with patch('chat_engine.requests.post',side_effect=fake_post):
                res=store.start_send(cid,'Analizá estos archivos',[img['id'],doc['id'],pdf['id'],code['id'],vid['id']],profile)
                for _ in range(30):
                    st=store.get_request(res['request_id'])
                    if st['status']!='running':break
                    time.sleep(0.05)
                self.assertEqual(st['status'],'done')
                self.assertEqual(st['content'],'Análisis completado.')
                self.assertEqual(len(calls),1)
                self.assertEqual(st['tokens'],0)
                self.assertEqual(st['tps'],0)

            zip_target=root/'export.zip'
            store.export_zip(cid,zip_target)
            with zipfile.ZipFile(zip_target) as z:
                names=z.namelist()
                self.assertIn('conversacion.md',names)
                self.assertIn('conversacion.json',names)
                self.assertTrue(any(n.endswith('captura.png') for n in names))
                md_text=z.read('conversacion.md').decode('utf-8')
                self.assertIn('Análisis completado.',md_text)

if __name__=='__main__':
    unittest.main()

class OfficeExtractionLimitsTests(unittest.TestCase):
    def test_rejects_compressed_document_before_parsing_oversized_xml(self):
        from chat_engine import _extract_office_xml
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'large.docx'
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('word/document.xml',b' '*(4*1024*1024+1))
            with self.assertRaises(ValueError):_extract_office_xml(path,'.docx')

class ImageFailureTests(unittest.TestCase):
    def test_image_rejection_never_retries_without_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp));cid=store.create_conversation('rapido')['id']
            image=store.upload_attachment(cid,'test.png','image/png',base64.b64encode(_sample_png()).decode())
            with patch('chat_engine.requests.post',return_value=FakeStreamResponse(400)) as post:
                result=store.start_send(cid,'Describe la imagen',[image['id']],{'account':1,'model':'test'})
                for _ in range(30):
                    state=store.get_request(result['request_id'])
                    if state['status']!='running':break
                    time.sleep(.05)
                self.assertEqual(state['status'],'error');self.assertEqual(post.call_count,1)
                self.assertIn('no aceptó',state['error'])

class ChatInputValidationTests(unittest.TestCase):
    def test_bad_generation_options_do_not_save_phantom_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ChatStore(Path(tmp));cid=store.create_conversation('rapido')['id']
            for options in [{'temperature':float('nan')},{'max_tokens':0},{'max_tokens':999999}]:
                with self.assertRaises(ValueError):store.start_send(cid,'Test',[],{'account':1,'model':'test'},**options)
            self.assertEqual(store.get_conversation(cid)['messages'],[])

class EmptyResponseTests(unittest.TestCase):
 def test_reasoning_only_stream_is_error_not_success(self):
  with tempfile.TemporaryDirectory() as folder:
   store=ChatStore(Path(folder));conv=store.create_conversation('coder2','Empty response test')
   profile={'account':2,'model':'fixture','context':4096,'temperature':0.2,'output_tokens':64}
   response=FakeStreamResponse(200,['data: {"choices":[{"delta":{"reasoning":"only reasoning"}}]}','data: [DONE]'])
   with patch('chat_engine.requests.post',return_value=response):
    request=store.start_send(conv['id'],'Hello',[],profile)
    for _ in range(100):
     state=store.get_request(request['request_id'])
     if state['status']!='running':break
     time.sleep(0.01)
    self.assertEqual(state['status'],'error');self.assertIn('sin una respuesta visible',state['error'])
