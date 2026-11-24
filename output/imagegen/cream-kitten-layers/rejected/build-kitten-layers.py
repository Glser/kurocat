"""Prepare the separated 4K kitten plates (Pillow, NumPy and SciPy).

Generation masters live under scripts/assets/cream-kitten. This build is local
and deterministic; it never calls an image API or reads a credential.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / 'scripts/assets/cream-kitten'
ASSETS = ROOT / 'src/assets/cream-kitten'
SCALE = 2
BODY_SIZE = 600 * SCALE
ARM_WIDTH, ARM_HEIGHT = 102, 238
ARM_ROOT, ARM_TOE = (51, 30), (51, 228)
MOUSE_ROOT, MOUSE_TOE = (133, 389), (-15, 550)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def matte_fur(image):
    """Remove the dark generation backdrop, retaining only real fur coverage.

    The opaque interior is hole-filled, so texture/shadow cannot turn into ghost
    fur. Only the narrow exterior hair fringe gets fractional coverage. Color
    decontamination removes the dark backdrop before saving straight RGBA.
    """
    rgb = np.asarray(image.convert('RGB'), dtype=np.float32)
    bg = np.median(np.concatenate([rgb[:12,:12].reshape(-1,3),
                                  rgb[:12,-12:].reshape(-1,3)]), axis=0)
    core = ndimage.binary_fill_holes(np.max(rgb,axis=-1) > 160)
    # Keep components representing the subject, not isolated generation noise.
    labels, _ = ndimage.label(core)
    counts = np.bincount(labels.ravel()); counts[0] = 0
    core = counts[labels] > core.size * .005
    distance = ndimage.distance_transform_edt(~core)
    interior = ndimage.binary_erosion(core, iterations=3)
    _, nearest = ndimage.distance_transform_edt(~interior, return_indices=True)
    foreground = rgb[nearest[0],nearest[1]]
    direction = foreground-bg
    alpha = np.clip(np.sum((rgb-bg)*direction,axis=-1) /
                    np.maximum(np.sum(direction*direction,axis=-1),1),0,1)
    alpha[core] = 1
    alpha[distance>14] = 0
    alpha[alpha<.025] = 0
    clean = np.clip((rgb-bg*(1-alpha[...,None])) /
                    np.maximum(alpha[...,None],.025),0,255)
    clean[alpha==0] = 0
    return np.dstack((clean*alpha[...,None],alpha*255))


def premultiplied(image):
    return np.asarray(image.convert('RGBa'),dtype=np.float32)


def rgba(data):
    return Image.fromarray(np.clip(data,0,255).round().astype('uint8'),'RGBa').convert('RGBA')


def save(data, name):
    rgba(data).save(ASSETS/name, lossless=True, method=6)


def sample(data,x,y):
    h,w = data.shape[:2]
    valid = (x>=0)&(x<=w-1)&(y>=0)&(y<=h-1)
    x=np.clip(x,0,w-1.001); y=np.clip(y,0,h-1.001)
    ix=x.astype(int); iy=y.astype(int)
    u=(x-ix)[...,None];v=(y-iy)[...,None]
    p=(data[iy,ix]*(1-u)+data[iy,ix+1]*u)*(1-v) + \
      (data[iy+1,ix]*(1-u)+data[iy+1,ix+1]*u)*v
    return p*valid[...,None]


def build_body():
    generated = Image.open(MASTERS/'body-master.webp').resize((BODY_SIZE,BODY_SIZE),Image.Resampling.LANCZOS)
    body = matte_fur(generated)
    original = premultiplied(Image.open(ASSETS/'rest.webp').resize(generated.size,Image.Resampling.LANCZOS))
    # Original face, accessories and whiskers remain pixel-aligned. Only the
    # chest beneath the chin is replaced by the clean, paw-free plate.
    yy = (np.arange(BODY_SIZE)+.5)/SCALE
    mix = smooth((yy-340)/40)[:,None,None]
    result = original*(1-mix)+body*mix
    save(result,'neutral-body.webp')
    return result


def prepare_arm(image):
    image.thumbnail((1200,1800),Image.Resampling.LANCZOS)
    data = matte_fur(image)
    opaque = data[...,3]>180
    ys,xs=np.where(opaque)
    bounds=(max(0,xs.min()-12),max(0,ys.min()-12),
            min(image.width,xs.max()+13),min(image.height,ys.max()+13))
    cropped=rgba(data).crop(bounds)
    arm=premultiplied(cropped.resize((ARM_WIDTH*SCALE,ARM_HEIGHT*SCALE),Image.Resampling.LANCZOS))
    # Match the soft, warm exposure of the preserved portrait. The generated
    # limbs are photographed slightly darker than its white chest.
    arm[...,:3] = np.minimum(arm[...,:3]*np.array([1.12,1.10,1.08]), arm[...,3,None])
    # Both roots use the same short transition and live inside the opaque torso.
    yy=(np.arange(arm.shape[0])+.5)/SCALE
    arm *= smooth((yy-4)/56)[:,None,None]
    return arm


def build_arms():
    source=Image.open(MASTERS/'arms-master.webp').convert('RGB')
    mid=source.width//2
    arms=[prepare_arm(source.crop(box)) for box in
          [(0,0,mid,source.height),(mid,0,source.width,source.height)]]
    for side,arm in zip(('left','right'),arms):
        save(arm,f'{side}-arm.webp')
    # The original typing mesh consumes a 600-unit-wide plate cropped at y=330.
    # Both arms now share precisely the same width, height and wrist scale.
    plate=np.zeros((270*SCALE,600*SCALE,4),dtype=np.float32)
    for center,arm in zip((131,398),arms):
        left=(center-ARM_ROOT[0])*SCALE
        top=(568-ARM_TOE[1]-330)*SCALE
        plate[top:top+arm.shape[0],left:left+arm.shape[1]]=arm
    save(plate,'separate-forepaws.webp')
    # Rotate the very same left arm to the mouse. Transverse scale is unchanged;
    # the final paw band is rigid, with reach taken up only above the wrist.
    gy,gx=(np.indices((600*SCALE,800*SCALE),dtype=np.float32)+.5)/SCALE-.5
    gx-=200
    vx,vy=np.array(MOUSE_TOE)-MOUSE_ROOT
    length=np.hypot(vx,vy)
    along=((gx-MOUSE_ROOT[0])*vx+(gy-MOUSE_ROOT[1])*vy)/length
    across=((gx-MOUSE_ROOT[0])*vy-(gy-MOUSE_ROOT[1])*vx)/length
    wrist=170
    native_length=ARM_TOE[1]-ARM_ROOT[1]
    paw_length=ARM_TOE[1]-wrist
    sy=np.where(along<length-paw_length,
                ARM_ROOT[1]+along*(wrist-ARM_ROOT[1])/(length-paw_length),
                ARM_TOE[1]+along-length)
    mouse=sample(arms[0],(ARM_ROOT[0]+across)*SCALE,sy*SCALE)
    save(mouse,'mouse-arm.webp')
    return arms,mouse


if __name__=='__main__':
    build_body()
    if (MASTERS/'arms-master.webp').exists():
        build_arms()
    print('Kitten layers prepared from saved masters.')
