"""Composite the approved chest edit without altering silhouette or face pixels."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parent
base = Image.open(ROOT/'before-rest.webp').convert('RGBA')
edit = Image.open(ROOT/'chest-1.png').convert('RGB').resize(base.size, Image.Resampling.LANCZOS)
mask = Image.new('L', base.size)
ImageDraw.Draw(mask).polygon([(165,675),(310,650),(495,680),(690,685),(735,999),(150,999)], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(9))
a = np.array(mask, dtype=np.float32)/255
original = np.array(base)
# Keep the original alpha matte exactly; only edit opaque interior fur.
a *= np.clip((original[:,:,3].astype(np.float32)-245)/10,0,1)
a[a < 1/255] = 0
out = original.copy()
out[:,:,:3] = np.round(original[:,:,:3]*(1-a[:,:,None]) + np.array(edit)*a[:,:,None]).astype('uint8')
result = Image.fromarray(out)
result.save(ROOT/'rest-clean.webp',lossless=True,exact=True,method=6)
mask.save(ROOT/'composite-mask.png')
board=Image.new('RGB',(1600,800),'#20262d')
for i,img in enumerate([base,result]):
 panel=Image.new('RGBA',(800,800),'#20262d')
 panel.alpha_composite(img.resize((800,800),Image.Resampling.LANCZOS))
 board.paste(panel.convert('RGB'),(i*800,0))
board.save(ROOT/'comparison.jpg',quality=95)
assert np.array_equal(out[:620],original[:620])
assert np.array_equal(out[:,:,3],original[:,:,3])
assert np.array_equal(out[a==0],original[a==0])
print('PASS: face, original alpha, and all pixels outside local chest mask unchanged')
