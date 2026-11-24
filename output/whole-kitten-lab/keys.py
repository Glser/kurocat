import subprocess,tempfile,re,base64,io
from PIL import Image
from pathlib import Path
out=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
 p=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless','--disable-gpu','--disable-extensions','--no-first-run','--user-data-dir='+profile,'--virtual-time-budget=7500','--dump-dom','http://127.0.0.1:1422/kurocat/@fs/D:/java/kurocat/output/whole-kitten-lab/keys.html'],capture_output=True,timeout=55)
s=p.stdout.decode(errors='replace'); frames=re.findall(r'data:image/png;base64,([a-zA-Z0-9+/=]+)',s);assert len(frames)==3,s[:1600]
for i,frame in enumerate(frames):
 im=Image.open(io.BytesIO(base64.b64decode(frame))).convert('RGBA');b=Image.new('RGB',im.size,'#e6e9ed');b.paste(im,mask=im.getchannel('A'));b.save(out/['escape.png','enter.png','numpad.png'][i]);print(i,im.getbbox())

