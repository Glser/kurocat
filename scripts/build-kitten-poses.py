"""Bake the kitten's typing poses from its own portrait, not from a second cat.

portrait.webp is the supplied photo with its background removed. rest.webp is
its repaired, prop-free chest plate. Coordinates below use a 600-unit portrait.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ASSETS = Path(__file__).resolve().parents[1] / 'src/assets/cream-kitten'
SIZE = 720


def smooth(x):
    t = np.clip(x, 0, 1)
    return t*t*(3-2*t)


def sample(im, x, y):
    """Bilinear inverse mapping from portrait units (the input is premultiplied)."""
    h, w = im.shape[:2]
    ix = np.clip((x + .5) * w / 600 - .5, 0, w-1.001)
    iy = np.clip((y + .5) * h / 600 - .5, 0, h-1.001)
    i, j = ix.astype(int), iy.astype(int)
    u, v = (ix-i)[..., None], (iy-j)[..., None]
    return (im[j,i]*(1-u) + im[j,i+1]*u)*(1-v) + (im[j+1,i]*(1-u) + im[j+1,i+1]*u)*v


def pixels(name):
    return np.asarray(Image.open(ASSETS/name).convert('RGBa'), dtype=np.float32)


def rgba(p):
    return Image.fromarray(np.clip(p,0,255).round().astype('uint8'), 'RGBa').convert('RGBA')


def build():
    source = pixels('portrait.webp')
    interior = Image.fromarray(source[...,3].astype('uint8')).resize((300,300)).filter(ImageFilter.MinFilter(13)).filter(ImageFilter.GaussianBlur(3))
    interior = np.asarray(interior, dtype=np.float32)[...,None] / 255
    yy, xx = (np.indices((SIZE,SIZE), dtype=np.float32) + .5)*600/SIZE - .5
    chest_photo = pixels('rest.webp')
    chest = sample(chest_photo, xx, yy)
    forepaws = np.zeros((SIZE, SIZE, 4), dtype=np.float32)
    # Follow the surviving contour of the real paw, wrist and forearm. The
    # prop hides the inner toe edges: gently expand nearby fur across that gap.
    y_marks = [340,351,366,376,390,410,427,436,447,455,466,478,490,500,508,517,532,551]
    visible = [125,150,159,175,191,197,197,195,202,223,227,220,214,201,182,169,159,145]
    rounded = [125,150,166,184,201,210,215,218,228,232,234,228,220,207,185,169,159,145]
    for cx,cy,angle,scale,mirror in [(125,489,64,.77,1),(397,500,77,.69,-1)]:
        a=np.deg2rad(angle); dx=(xx-cx)*mirror/scale; dy=(yy-cy)/scale
        x=135+dx*np.cos(a)+dy*np.sin(a); y=442-dx*np.sin(a)+dy*np.cos(a)
        edge=np.interp(y,y_marks,rounded); inner=np.interp(y,y_marks,visible)
        sx=x-(edge-inner)*smooth((x-129)/np.maximum(edge-129,1))
        fur=sample(source,sx,y)
        # Long feather at the shoulder and elbow. Toe borders retain their detail.
        mask=smooth((x-64)/72)*smooth((y-344)/58)*smooth((548-y)/49)*smooth((edge-x)/4.8)
        alpha=mask[...,None]*sample(interior,sx,y)
        if mirror < 0:
            fur[...,:3] *= .967
        # Include the matching strip of chest fur behind the wrist. This part
        # takes up the reach while the actual toes keep their native shape.
        shoulder_x = cx + (-12 if mirror > 0 else 15)
        sleeve = smooth((yy-354)/68)*smooth((509-yy)/44)*smooth((58-abs(xx-shoulder_x))/27)
        arm = fur*alpha + chest*sleeve[...,None]*(1-alpha*fur[...,3:4]/255)
        forepaws = arm + forepaws*(1-arm[...,3:4]/255)
        if mirror > 0:
            # On the desk there is no torso behind the arm. Keep a solid fur
            # core with a narrow soft outline; feather only its joint into the cat.
            t = np.clip((yy-365)/154, 0, 1)
            radius = 38 + 9*np.sin(np.pi*t)
            center = shoulder_x + 5*np.sin(np.pi*t)
            dome = ((xx-center)/radius)**2 + (np.maximum(400-yy,0)/39)**2
            grip_sleeve = smooth((1-dome)/.20)*smooth((525-yy)/45)
            # Sample inside the coat: the desktop-coloured cutout fringe on the
            # silhouette must not become a streak when the shoulder rotates.
            grip_coat = sample(chest_photo, xx+44, yy)
            grip = fur*alpha + grip_coat*grip_sleeve[...,None]*(1-alpha*fur[...,3:4]/255)
            # Bake one fixed, foreshortened grip into the chest at source resolution.
            # The canvas includes 200 portrait units of transparent space to the left.
            gy,gx = (np.indices((900,1200), dtype=np.float32)+.5)/1.5-.5
            gx -= 200
            tx,ty = -67,577  # contact landmark in the original 600-unit body space
            ax,ay = 94,437
            length = np.hypot(tx-ax,ty-ay)
            c,sn = (ty-ay)/length,(ax-tx)/length
            scale = length/(564-376)
            u = 131 + (c*(gx-ax)+sn*(gy-ay))/scale
            v = 376 + (-sn*(gx-ax)+c*(gy-ay))/scale
            hand = sample(grip,u,v)
            hand *= ((u>=0)&(u<600)&(v>=0)&(v<600))[...,None]
            body = sample(chest_photo,gx,gy)*((gx>=0)&(gx<600))[...,None]
            # Reveal the original stationary chest fur over the proximal joint.
            socket = smooth((1-np.hypot((gx-ax)/97,(gy-ay)/85))/.55)[...,None]
            hand *= 1-body[...,3:4]/255*socket
            rgba(hand + body*(1-hand[...,3:4]/255)).save(ASSETS/'mouse-pose.webp',quality=97,method=6)
    # Keep the real silhouette when the toes cross the keyboard bezel. The
    # torso is already present in rest.webp; no rectangular chest pixels here.
    rgba(forepaws).crop((0, 396, SIZE, SIZE)).save(ASSETS/'native-forepaws.webp',quality=97,method=6)


if __name__=='__main__':
    build()
