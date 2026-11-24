from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import map_coordinates, gaussian_filter
root=Path('output/kitten-chest-cleanup')
base=Image.open(root/'before-rest.webp').convert('RGBA')
p=np.array(base); yy,xx=np.indices(p.shape[:2],dtype=np.float32)
# Sample nearby unbroken chest fur to replace the raised diagonal old paw.
sx=170+(xx-380)*.675; sy=yy-25
rgb=np.stack([map_coordinates(p[:,:,c].astype(float),[sy,sx],order=1,mode='nearest') for c in range(3)],axis=-1)
mask=Image.new('L',base.size);d=ImageDraw.Draw(mask)
d.polygon([(430,708),(550,718),(688,781),(750,902),(760,999),(420,999),(383,895),(399,791)],fill=255)
a=np.array(mask.filter(ImageFilter.GaussianBlur(18)),dtype=float)/255
# Match overall fur exposure, preserving donor hair detail.
rgb=np.clip(rgb+np.array([3,2,1]),0,255)
a*=np.clip((p[:,:,3].astype(float)-245)/10,0,1); a[a<1/255]=0
out=p.copy();out[:,:,:3]=np.round(p[:,:,:3]*(1-a[:,:,None])+rgb*a[:,:,None]).astype('uint8')
result=Image.fromarray(out); result.save(root/'rest-clean.webp',lossless=True,exact=True,method=6)
board=Image.new('RGB',(1400,700),'#252b32')
for i,im in enumerate([base,result]):
 panel=Image.new('RGBA',(700,700),'#252b32'); panel.alpha_composite(im.resize((700,700),Image.Resampling.LANCZOS)); board.paste(panel.convert('RGB'),(700*i,0))
board.save(root/'local-comparison.jpg',quality=95)
assert np.array_equal(out[:620],p[:620]); assert np.array_equal(out[:,:,3],p[:,:,3])
print('Local chest candidate saved; face and alpha preserved')

