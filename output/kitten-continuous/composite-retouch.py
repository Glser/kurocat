from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/kitten-continuous'

def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)

def composite():
    original=Image.open(OUT/'before-mouse-pose.webp').convert('RGBA')
    raw=Image.open(OUT/'joint-1.png').convert('RGB').resize(original.size,Image.Resampling.LANCZOS)
    rgb=np.asarray(raw,dtype=np.float32)
    bg=np.median(rgb[:,:110],axis=1)[:,None,:]
    core=ndimage.binary_fill_holes(np.max(rgb,axis=-1)>140)
    inner=ndimage.binary_erosion(core,iterations=2)
    dist,indices=ndimage.distance_transform_edt(~inner,return_indices=True)
    fg=rgb[indices[0],indices[1]]
    direction=fg-bg
    alpha=np.clip(np.sum((rgb-bg)*direction,axis=-1)/np.maximum(np.sum(direction*direction,axis=-1),1),0,1)
    alpha[inner]=1
    alpha[dist>9]=0
    alpha[alpha<.025]=0
    color=np.clip((rgb-bg*(1-alpha[...,None]))/np.maximum(alpha[...,None],.025),0,255)
    patched=np.dstack((color*alpha[...,None],alpha*255))
    yy,xx=np.indices(alpha.shape,dtype=np.float32)
    # Only the existing foreleg and a short inside-chest overlap are replaced.
    # The original face, accessories and opposite side are byte-preserved.
    region=smooth((yy-520)/95)*(1-smooth((xx-550)/145))
    base=np.asarray(original.convert('RGBa'),dtype=np.float32)
    result=base*(1-region[...,None])+patched*region[...,None]
    result=Image.fromarray(np.clip(result,0,255).round().astype('uint8'),'RGBa').convert('RGBA')
    exact=np.array(result)
    original_pixels=np.asarray(original)
    exact[region==0]=original_pixels[region==0]
    result=Image.fromarray(exact,'RGBA')
    result.save(OUT/'retouched-pose.webp',lossless=True,method=6)
    out=Image.new('RGB',(1600,1200))
    for i,path in enumerate([OUT/'before-mouse-pose.webp',OUT/'retouched-pose.webp']):
        im=Image.open(path).convert('RGBA');im.thumbnail((800,600))
        for j,bg in enumerate(['#18212b','#f0f0ef']):
            panel=Image.new('RGBA',(800,600),bg);panel.alpha_composite(im)
            out.paste(panel.convert('RGB'),(i*800,j*600))
    out.save(OUT/'retouch-comparison.jpg')

if __name__=='__main__':composite()
