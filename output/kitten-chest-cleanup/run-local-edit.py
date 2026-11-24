from pathlib import Path
import base64, json, re, runpy, urllib.request, urllib.error, sys
ROOT=Path(__file__).resolve().parent
job=sys.argv[1] if len(sys.argv)>1 else 'scene'
credentials=Path('D:/java/密钥.txt').read_text(encoding='utf-8-sig')
key=re.search(r'\bsk-[A-Za-z0-9_-]+',credentials).group()
client=runpy.run_path('D:/codex/skills/oioi-image-generate/scripts/image_client.py')
model_req=urllib.request.Request('https://api.oioi.lat/v1/models',headers={'Authorization':'Bearer '+key,'User-Agent':'Mozilla/5.0'})
with urllib.request.urlopen(model_req,timeout=60) as model_response:
 models=json.loads(model_response.read())
if 'nano-banana-2' not in [item.get('id') for item in models.get('data',[])]: raise SystemExit('Requested image model is unavailable')
print('Requested image model verified.',flush=True)
allowed,message=client['check_rate_limit']()
if not allowed: raise SystemExit(message)
paths=[str(ROOT/'edit-input.png'),str(ROOT/'edit-region.png')]
content=[{'type':'text','text':(ROOT/'request.txt').read_text(encoding='utf-8')}]
for path in paths:
 p=Path(path);mime='image/png' if p.suffix.lower()=='.png' else 'image/jpeg'
 content.append({'type':'image_url','image_url':{'url':'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()}})
plan='Remove the residual folded forepaws from the chest only, preserving all other assets and the original character.'
spec=(ROOT/(job+'-spec.txt')).read_text(encoding='utf-8')
payload={'model':'nano-banana-2','messages':[{'role':'system','content':spec},{'role':'user','content':content}], 'temperature':0.4,'extra_body':{'google':{'image_config':{'aspect_ratio':'1:1','image_size':'4K'}}}}
(ROOT/(job+'-settings.json')).write_text(json.dumps({'model':payload['model'],'resolution':'4K','aspect_ratio':'1:1','approved_plan':plan,'reference_files':paths},ensure_ascii=False,indent=2),encoding='utf-8')
request=urllib.request.Request('https://api.oioi.lat/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
client['update_rate_limit']()
print('Submitting nano-banana-2 4K with the original torso and a local chest repair guide.',flush=True)
try:
 with urllib.request.urlopen(request,timeout=360) as response:
  result=json.loads(response.read())
except urllib.error.HTTPError as e:
 print('Request failed:',e.code,e.read().decode()[:1500].replace(key,'[REDACTED]'))
 raise SystemExit(1)
except Exception as e:
 print('Request failed:',str(e).replace(key,'[REDACTED]'));raise SystemExit(1)
(ROOT/(job+'-response.json')).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
images=[]
def visit(value):
 if isinstance(value,dict):
  if 'b64_json' in value: images.append(('base64',value['b64_json']))
  for k,v in value.items():
   if k!='b64_json': visit(v)
 elif isinstance(value,list):
  for v in value: visit(v)
 elif isinstance(value,str):
  for x in re.findall(r'data:image/[^;]+;base64,([A-Za-z0-9+/=\r\n]+)',value): images.append(('base64',x))
  for x in re.findall(r'https?://[^\s\"\)<>]+',value):
   if any(t in x.lower() for t in ['.png','.jpg','.webp','image','cdn']): images.append(('url',x))
visit(result)
seen=set()
for kind,data in images:
 if data in seen: continue
 seen.add(data)
 if kind=='base64': raw=base64.b64decode(data)
 else:
  with urllib.request.urlopen(data,timeout=90) as response: raw=response.read()
 out=ROOT/f'{job}-{len(seen)}.png';out.write_bytes(raw)
 from PIL import Image
 im=Image.open(out);print('Saved:',out,'size:',im.size,flush=True)
 im.thumbnail((1200,1200));im.save(ROOT/f'{job}-preview-{len(seen)}.png')
print('image_count:',len(seen),'response_keys:',list(result.keys()),flush=True)
if not seen:
 for c in result.get('choices',[]):
  text=c.get('message',{}).get('content','')
  print(str(text)[:2500])
