"""Build the 4:3 photo trial sprites: python prepare_reach.py PATH_TO_NEW_PHOTO.png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

out = Path(__file__).resolve().parent
# Coordinates are measured in the reference photograph, in a 912 x 684 space.
s = 2
im = Image.open(sys.argv[1]).convert('RGB')
if im.width * 3 != im.height * 4:
    raise ValueError('Expected the 4:3 goggles kitten reference')
im = im.resize((912*s, 684*s), Image.Resampling.LANCZOS)
rgb = np.asarray(im, dtype=np.float32)
y, x = np.indices(rgb.shape[:2], dtype=np.float32)/s

def clamp(a): return np.clip(a, 0, 1)

def mask(points, blur):
    m = Image.new('L', im.size)
    ImageDraw.Draw(m).polygon([(round(i*s),round(j*s)) for i,j in points], fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur*s)), dtype=np.float32)/255

def save(name, color, alpha, box=None):
    img = Image.fromarray(np.dstack((color,alpha*255)).clip(0,255).round().astype('uint8'))
    if box: img = img.crop(tuple(n*s for n in box))
    img.save(out/name, quality=96, method=6)

# Keep the black headband and earcups opaque. Recover fine cream hairs against
# the blue-grey background from their red-channel contrast outside the contour.
outline = [(325,-2),(359,-2),(389,16),(405,27),(428,19),(471,13),(510,12),(552,18),(599,30),(637,53),(658,61),(685,49),(716,40),(756,29),(751,58),(743,108),(736,136),(744,156),(752,178),(754,198),(750,215),(771,230),(784,254),(786,283),(779,320),(765,356),(746,388),(723,405),(700,411),(674,411),(683,439),(695,473),(700,507),(710,544),(716,593),(712,652),(175,639),(177,606),(188,558),(202,526),(215,488),(230,454),(252,414),(257,382),(260,344),(256,314),(237,299),(220,284),(208,266),(201,246),(200,214),(205,185),(215,155),(231,130),(250,111),(270,101),(294,94),(308,77),(327,61)]
core = mask(outline,1.5)
halo = mask(outline,9)
fur = clamp((rgb[:,:,0]-62)/132)
alpha = np.maximum(core, clamp(halo*4)*fur)
# Cat meets the source keyboard here; no original keys should travel with a paw.
base = np.interp(x, [0,180,223,362,463,596,706,912], [624,626,632,641,644,649,652,654])
body_alpha = alpha * clamp((base-y)/1.5)
# Trace only the palm visible in the photo. Coordinates above the rounded
# knuckle outline belong to the chest, not to a rigid moving foot.
body = rgb.copy()
rest_alpha = body_alpha.copy()
for side,cx,rows in [
 ('left',298,[(517,274,285),(519,266,297),(525,250,314),(535,238,331),
              (550,229,347),(566,224,358),(589,222,369),(609,223,373),
              (626,226,372),(640,232,363),(650,245,350),(656,263,337)]),
 ('right',535,[(542,556,569),(544,546,581),(549,532,591),(559,516,599),
               (575,499,607),(592,483,609),(612,471,607),(629,465,604),
               (646,463,598),(657,470,589),(668,487,573)])]:
    rows=np.asarray(rows); l=np.interp(y,rows[:,0],rows[:,1]); r=np.interp(y,rows[:,0],rows[:,2]);
    cap=rows[0,0]; end=rows[-1,0]; feather=2+4*clamp((615-y)/68)
    a=clamp((x-l)/feather)*clamp((r-x)/feather)*clamp((y-cap)/3)*clamp((end-y+1)/2)
    contact=clamp((rgb[:,:,0]-51)/110)
    a*=alpha*(1-clamp((y-base+4)/6)*(1-contact))
    save(side+'-reach.webp',rgb,a,(cx-95,cap,cx+95,end+2))
    rest_alpha=np.maximum(rest_alpha,a)
    # Patch the empty space only when this side actually leaves its rest pose.
    mix=clamp((y-cap+12)/16)*clamp((x-l+20)/18)*clamp((r+20-x)/18)
    sample_y=np.clip((cap-12-(y-cap)*.46)*s,0,im.height-1).astype(int)
    fur_patch=rgb[sample_y,(x*s).astype(int)]
    if side == 'left':
        # Clear the old knuckle shadow as well as the paw. Borrow clean chest
        # fur from inside the silhouette, never the dark photo background.
        mix=clamp((y-484)/40)*clamp((414-x)/34)*clamp((x-155)/22)
        mix=mix*mix*(3-2*mix)
        donor_x=260+.7*(x-175)+16*clamp((y-490)/155)
        donor_y=420+(y-440)*.34
        fur_patch=rgb[(donor_y*s).astype(int),(donor_x*s).astype(int)]
        # One continuous strip from shoulder through toes. Beyond the wrist
        # follow the existing paw matte unchanged; the renderer splits this
        # plate at a shared row rather than layering two different fur crops.
        knots=[425,444,468,492,512,528,542,555,567,585]
        axis=np.interp(y,knots,[282,282,282,282,283,284,287,290,292,295])
        radius=np.interp(y,knots,[26,46,57,58,56,54,57,61,65,70])
        # Let local fur grain break up the edge instead of a smooth tube.
        detail=rgb[:,:,0]-np.asarray(im.filter(ImageFilter.GaussianBlur(3*s)))[:,:,0]
        edge=clamp((radius-abs(x-axis)+np.clip(detail*.35,-2,2))/5)
        proximal=edge*clamp((y-425)/38)*alpha
        wrist=clamp((y-535)/38); wrist=wrist*wrist*(3-2*wrist)
        limb=proximal*(1-wrist)+a*wrist
        save('mouse-foreleg.webp',rgb,limb,(cx-100,425,cx+100,end+2))
    body=body*(1-mix[:,:,None])+fur_patch*mix[:,:,None]
    # Narrow strip of actual upper-leg fur to bridge shoulder and moving palm.
    # Fade all edges and cap its width well inside the palm silhouette.
    shoulder=278 if side=='left' else 576
    t=clamp((y-(cap-76))/76); axis=shoulder+(cx-shoulder)*t
    sleeve=clamp((35-abs(x-axis))/9)*clamp((y-cap+76)/22)*clamp((cap+12-y)/10)*alpha
    save(side+'-sleeve.webp',rgb,sleeve,(cx-100,cap-76,cx+100,cap+12))
save('rest-photo.webp',rgb,rest_alpha)
save('reach-body.webp',body,body_alpha)
