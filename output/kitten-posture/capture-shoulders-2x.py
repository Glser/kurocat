import base64,subprocess,json,re,sys,tempfile
from pathlib import Path
from PIL import Image
from io import BytesIO
out=Path('output/kitten-posture')
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
 p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless','--disable-gpu','--force-device-scale-factor=2','--disable-extensions','--no-first-run','--user-data-dir='+profile,'--virtual-time-budget=6000','--dump-dom','http://localhost:1436/output/kitten-posture/check.html'],capture_output=True)
s=p.stdout.decode(errors='replace'); data=re.findall(r'data:image/png;base64,([a-zA-Z0-9+/=]+)',s);assert len(data)==6,s[:500];
for idx in [3,4,5]:
 im=Image.open(BytesIO(base64.b64decode(data[idx]))).convert('RGBA'); bg=Image.new('RGB',im.size,'#202731'); bg.paste(im,mask=im.getchannel('A')); bg.crop((125,203,727,785)).save(out/(sys.argv[1]+str(idx)+'.png'))
