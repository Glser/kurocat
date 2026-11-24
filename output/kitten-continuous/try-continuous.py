from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy.interpolate import PchipInterpolator
import importlib.util

spec=importlib.util.spec_from_file_location('poses','scripts/build-kitten-poses.py')
poses=importlib.util.module_from_spec(spec);spec.loader.exec_module(poses)
source=poses.pixels('portrait.webp');chest=poses.pixels('rest.webp')
gy,gx=(np.indices((900,1200),dtype=np.float32)+.5)/1.5-.5
gx-=200
# One continuous photographic foreleg: root, wrist and toe stay in the same
# image rather than joining a second sleeve to a separately rotated paw.
root=np.array([88.,472.]);toe=np.array([227.,465.])
target_root=np.array([85.,465.]);target_toe=np.array([-25.,565.])
sv=toe-root;tv=target_toe-target_root
su=sv/np.linalg.norm(sv);tu=tv/np.linalg.norm(tv)
along=(gx-target_root[0])*tu[0]+(gy-target_root[1])*tu[1]
across=(gx-target_root[0])*(-tu[1])+(gy-target_root[1])*tu[0]
stretch=np.linalg.norm(tv)/np.linalg.norm(sv)
sx=root[0]+along/stretch*su[0]-across/1.02*su[1]
sy=root[1]+along/stretch*su[1]+across/1.02*su[0]
xs=[50,80,105,130,155,180,200,215,225,232]
top=PchipInterpolator(xs,[440,436,436,438,440,442,445,448,452,463])(np.clip(sx,50,232))
bottom=PchipInterpolator(xs,[514,515,513,509,506,502,494,483,475,463])(np.clip(sx,50,232))
alpha=poses.smooth((sy-top)/1.6)*poses.smooth((bottom-sy)/1.6)*poses.smooth((sx-50)/16)*poses.smooth((232-sx)/1.6)
hand=poses.sample(source,sx,sy)*alpha[...,None]
body=poses.sample(chest,gx,gy)*((gx>=0)&(gx<600))[...,None]
# Place the root under the opaque chest; only the short inside overlap blends.
join=poses.smooth((sx-75)/44)[...,None]
hand*=1-(body[...,3:4]/255)*(1-join)
result=poses.rgba(hand+body*(1-hand[...,3:4]/255))
result.save('output/kitten-continuous/candidate.webp',lossless=True)
out=Image.new('RGB',(1600,600),'#303943')
for i,path in enumerate(['output/kitten-continuous/before-mouse-pose.webp','output/kitten-continuous/candidate.webp']):
 im=Image.open(path).convert('RGBA');im.thumbnail((800,600));out.paste(im,(i*800,0),im)
out.save('output/kitten-continuous/candidate.jpg')
