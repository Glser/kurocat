from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.interpolate import CubicSpline

out = Path(__file__).resolve().parent
scale = 1.5
im = Image.open(sys.argv[1]).convert('RGB').resize((1440, 960),Image.Resampling.LANCZOS)
rgb = np.asarray(im, dtype=np.float32)
outline = [(348,-10),(399,-8),(427,27),(467,19),(505,16),(562,22),(615,40),(657,62),(680,79),(704,62),(739,47),(768,39),(766,86),(756,133),(752,152),(769,171),(778,190),(773,216),(798,236),(808,270),(800,313),(783,358),(755,399),(732,411),(688,409),(683,422),(690,456),(700,500),(705,555),(714,598),(717,647),(174,647),(183,603),(196,559),(217,515),(235,463),(245,426),(265,390),(280,357),(281,322),(265,301),(243,281),(227,253),(224,214),(230,175),(244,137),(270,106),(298,92),(316,92),(326,71),(350,48)]
p=np.array(outline+[outline[0]],float); d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]; pts=CubicSpline(d,p,bc_type='periodic')(np.linspace(0,d[-1],1600))*scale
mask=Image.new('1',im.size);ImageDraw.Draw(mask).polygon([tuple(v) for v in pts],fill=1);mask=np.array(mask)
fg=ndi.distance_transform_edt(mask)>12*scale; bg=ndi.distance_transform_edt(~mask)>17*scale
_,fi=ndi.distance_transform_edt(~fg,return_indices=True);_,bi=ndi.distance_transform_edt(~bg,return_indices=True)
f=rgb[tuple(fi)]; b=rgb[tuple(bi)]; vec=f-b
alpha=np.clip(((rgb-b)*vec).sum(2)/np.maximum((vec*vec).sum(2),32),0,1)
alpha[fg]=1;alpha[bg]=0
# Separate the tabletop from the natural toe contours in the bottom band.
y,x=np.indices(alpha.shape)/scale
# White chest fur over the dark studio wall. Estimate the foreground from
# deeper inside the coat so dark gaps between guard hairs stay transparent.
inner=ndi.distance_transform_edt(mask)>45*scale
_,ii=ndi.distance_transform_edt(~inner,return_indices=True)
coat=rgb[tuple(ii)]; axis=coat-b
coverage=np.clip(((rgb-b)*axis).sum(2)/np.maximum((axis*axis).sum(2),32),0,1)
edge=np.clip((48*scale-ndi.distance_transform_edt(mask))/(12*scale),0,1)
chest=np.clip((y-np.where(x<455,315,415))/14,0,1)*edge
alpha=alpha*(1-chest)+np.where(bg,0,coverage)*chest
base=625.5+.009*(x-174)
alpha*=np.clip((base-y)*1.4+.5,0,1)
color=np.clip((rgb-b*(1-alpha[...,None]))/np.maximum(alpha[...,None],.02),0,255)
rgba=Image.fromarray(np.dstack([color,alpha*255]).round().astype('uint8'))
rgba.save(out/'whole-kitten.webp',quality=96,method=6)
# Foreground toe tips use the same registered photo. Only these fur islands
# cross the rear lip of the keyboard; the cut base remains behind the case.
toes=np.zeros_like(alpha)
for cx,cy,rx,ry in [(322,611,72,50),(567,616,68,47)]:
 r=((x-cx)/rx)**2+((y-cy)/ry)**2;toes=np.maximum(toes,np.clip((1-r)*8,0,1))
arr=np.array(rgba);arr[:,:,3]=np.rint(alpha*toes*255);Image.fromarray(arr).save(out/'toe-tips.webp',quality=96,method=6)
# A short strip of contact poses. Only distal fur moves, tapering smoothly
# to zero at the chest and between the paws. Keep both layers registered.
for filename in ('whole-kitten','toe-tips'):
    source=np.asarray(Image.open(out/(filename+'.webp')).convert('RGBa'))
    yy,xx=np.indices((round(226*scale),source.shape[1]),dtype=np.float32)
    yy+=round(430*scale)
    weight=np.maximum(np.exp(-((xx/scale-322)/80)**4),np.exp(-((xx/scale-567)/78)**4))
    weight*=np.clip((yy/scale-434)/143,0,1)**2
    atlas=Image.new('RGBA',(source.shape[1],yy.shape[0]*5))
    for frame in range(5):
        coords=[yy-weight*frame*3.7*scale,xx]
        px=np.stack([ndi.map_coordinates(ch,coords,order=1) for ch in source.transpose(2,0,1)],axis=-1)
        atlas.paste(Image.fromarray(px,'RGBa').convert('RGBA'),(0,frame*yy.shape[0]))
    atlas.save(out/(filename+'-contacts.webp'),quality=95,method=6)

