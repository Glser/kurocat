from pathlib import Path
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates

folder = Path(__file__).resolve().parent
photo = np.array(Image.open(folder/'whole-kitten.webp').convert('RGBA'))
h,w = photo.shape[:2]
y,x = np.indices((h,w),dtype=np.float32)/1.5
body = photo.copy()
for side,cx,toe,ys,left,right in [
    ('left',322,625,[401,460,525,555,579,600,619,629],[254,253,257,250,247,246,250,268],[329,351,368,384,397,401,398,379]),
    ('right',567,627,[405,465,525,558,582,603,621,632],[581,562,537,518,500,493,493,506],[653,646,630,623,633,637,634,616])]:
    def edge(points): return PchipInterpolator(ys,points)(np.clip(y,ys[0],ys[-1]))
    # Follow the toe silhouette and round off the small area cut by the tabletop.
    xn=(x-cx)/(77 if side=='left' else 74)
    bottom=toe-12*np.abs(xn)**3-1.6*np.cos((x-cx)*.15)
    feather=2.3+12*np.clip((565-y)/100,0,1)
    opacity=np.clip((x-edge(left))/feather,0,1)*np.clip((edge(right)-x)/feather,0,1)
    opacity*=np.clip((bottom-y)/1.4,0,1)*np.clip((y-ys[0])/66,0,1)
    arm=photo.copy();arm[:,:,3]=np.round(photo[:,:,3]*opacity)
    # Keep a common origin for the strips used by the animated joints.
    arm_image=Image.fromarray(arm);arm_image.crop((int((cx-122)*1.5),600,int((cx+122)*1.5),954)).save(folder/(side+'-reach.webp'),quality=97)
    # Reconstruct fur behind each resting paw using the coat just above it.
    patch_y=np.minimum(y,525-(y-525)*.35)
    mix=np.clip((y-526)/26,0,1)*np.clip((x-edge(left)+34)/22,0,1)*np.clip((edge(right)+34-x)/22,0,1)
    for ch in range(3):
        fur=map_coordinates(photo[:,:,ch],[patch_y*1.5,x*1.5],order=1,mode='nearest'); body[:,:,ch]=np.round(body[:,:,ch]*(1-mix)+fur*mix)
Image.fromarray(body).save(folder/'reach-body.webp',quality=97)

