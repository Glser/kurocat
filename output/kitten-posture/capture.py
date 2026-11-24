import base64,subprocess,json,re,sys,tempfile
from pathlib import Path
from PIL import Image
from io import BytesIO
out=Path('output/kitten-posture')
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
 p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless','--disable-gpu','--disable-extensions','--no-first-run','--user-data-dir='+profile,'--virtual-time-budget=6000','--dump-dom','http://localhost:1436/output/kitten-posture/check.html'],capture_output=True)
s=p.stdout.decode(errors='replace'); data=re.findall(r'data:image/png;base64,([a-zA-Z0-9+/=]+)',s);assert len(data)==6,s[:500]; b=Image.new('RGB',(540*3,456*2),'#e8ebef');
for i,d in enumerate(data):
 im=Image.open(BytesIO(base64.b64decode(d))).convert('RGBA');b.paste(im,(i%3*540,i//3*456),im)
b.save(out/(sys.argv[1]+'.png'))
