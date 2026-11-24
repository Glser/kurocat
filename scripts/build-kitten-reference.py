"""Extract the user-approved reference without regenerating facial features."""
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'scripts/assets/cream-kitten/face-reference.png'
ASSETS=ROOT/'src/assets/cream-kitten'

def build():
    image=Image.open(MASTER).convert('RGB')
    rgb=np.asarray(image,dtype=np.float32)
    h,w=rgb.shape[:2]
    y,x=np.indices((h,w))
    # Light fur encloses the dark eyes and goggle hardware; fill those interiors.
    core=ndimage.binary_fill_holes(np.max(rgb,axis=-1)>np.where(y>700,165,125))
    # Lower chest shadows reach the image boundary and are not enclosed holes.
    core |= (y>900)&(x>330)&(x<830)
    # Preserve the black headset crown between the ears, based on its actual
    # silhouette in the original aligned portrait matte, never a bright threshold.
    original=np.array(Image.open(ASSETS/'portrait.webp').convert('RGBA').resize(image.size,Image.Resampling.LANCZOS))
    headset=((y<230)&(x>330)&(x<1020)) | ((x>960)&(y>220)&(y<710)) | ((x<360)&(x>170)&(y>80)&(y<520))
    core |= headset & (original[:,:,3]>240) & (rgb[:,:,2]-rgb[:,:,0]<12)
    core=ndimage.binary_fill_holes(core)
    labels,_=ndimage.label(core)
    counts=np.bincount(labels.ravel()); counts[0]=0
    core=counts[labels] > h*w*.005
    # Fur edge samples still contain the dark source backdrop. Sample deeper
    # inside the coat so unmixing removes that tint instead of preserving it.
    inner=ndimage.binary_erosion(core,iterations=12)
    inner |= ndimage.binary_erosion(core,iterations=3) & headset
    dist,nearest=ndimage.distance_transform_edt(~inner,return_indices=True)
    foreground=rgb[nearest[0],nearest[1]]
    # Use nearby exterior background color to unmix only the fine fur fringe.
    far=ndimage.binary_dilation(core,iterations=12)
    _,background_indices=ndimage.distance_transform_edt(far,return_indices=True)
    background=rgb[background_indices[0],background_indices[1]]
    direction=foreground-background
    alpha=np.clip(np.sum((rgb-background)*direction,axis=-1)/np.maximum(np.sum(direction*direction,axis=-1),1),0,1)
    alpha[inner]=1
    alpha[dist>20]=0
    alpha[alpha<.03]=0
    color=np.clip((rgb-background*(1-alpha[:,:,None]))/np.maximum(alpha[:,:,None],.03),0,255)
    color[inner]=rgb[inner]
    rgba=np.dstack((color,alpha*255)).round().astype('uint8')
    assert np.array_equal(rgba[350:690,380:925,:3],rgb[350:690,380:925].astype('uint8'))
    result=Image.fromarray(rgba)
    result.save(ASSETS/'reference-body.webp',lossless=True,exact=True,method=6)
    print('PASS: reference face pixels preserved exactly')
    board=Image.new('RGB',(1200,600))
    for i,bg in enumerate(['#20262e','#eceef1']):
        panel=Image.new('RGBA',(600,600),bg)
        panel.alpha_composite(result.resize((600,600),Image.Resampling.LANCZOS))
        board.paste(panel.convert('RGB'),(600*i,0))
    preview_dir=ROOT/'output/kitten-reference-face'
    preview_dir.mkdir(parents=True,exist_ok=True)
    board.save(preview_dir/'matte-check.jpg',quality=95)
if __name__=='__main__':build()
