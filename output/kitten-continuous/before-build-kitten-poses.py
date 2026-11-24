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
        arm_scale = scale  # keep the loop's arm-warp scale; `scale` is reused below
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
            # Bake one fixed, foreshortened grip by mapping each OUTPUT pixel
            # straight back to the portrait source in ONE bilinear sample.
            # The previous version chained two resamples (source -> 720px
            # warp grid -> output) which blurred the arm into a ghost.
            # Canvas: 1200x900 px = 800x600 body units at 1.5x, including
            # 200 body units of transparent space to the left.
            gy, gx = (np.indices((900, 1200), dtype=np.float32) + .5) / 1.5 - .5
            gx -= 200
            tx, ty = -67, 577  # contact landmark in the original 600-unit body space
            ax, ay = 94, 437
            length = np.hypot(tx - ax, ty - ay)
            c, sn = (ty - ay) / length, (ax - tx) / length
            scale = length / (564 - 376)
            # Output grid -> grip-pose grid (u,v) -> arm source coords (sx,y),
            # composing both rotations into a single sampling chain.
            u = 131 + (c * (gx - ax) + sn * (gy - ay)) / scale
            v = 376 + (-sn * (gx - ax) + c * (gy - ay)) / scale
            du = (u - cx) * mirror / arm_scale
            dv = (v - cy) / arm_scale
            x = 135 + du * np.cos(a) + dv * np.sin(a)
            y = 442 - du * np.sin(a) + dv * np.cos(a)
            edge = np.interp(y, y_marks, rounded)
            inner = np.interp(y, y_marks, visible)
            sx = x - (edge - inner) * smooth((x - 129) / np.maximum(edge - 129, 1))
            arm_fur = sample(source, sx, y)
            # The toe lands 2-3 units inside the silhouette edge, where the
            # eroded `interior` alpha and the 4.8-unit edge feather both fade
            # to ~0 (double penalty -> ghost arm). The grip path instead uses
            # the portrait's OWN alpha (its cutout edge is already clean) and
            # a relaxed feather; pixels beyond the photo edge vanish via the
            # source alpha itself.
            arm_mask = smooth((sx - 64) / 72) * smooth((y - 344) / 58) \
                * smooth((548 - y) / 49) * smooth((edge - sx) / 3.0)
            arm_alpha = arm_mask[..., None] * np.minimum(1.0, arm_fur[..., 3:4] * 1.08 / 255)
            hand = arm_fur * arm_alpha
            # Continue the original forearm into the shoulder. The old rounded
            # chest-texture capsule ended outside the torso and looked pasted on.
            # Its replacement extends underneath the chest; the exposed edge
            # follows actual fur from the same photographed foreleg.
            t = np.clip((v - 350) / 150, 0, 1)
            radius = 39 + 5 * np.sin(np.pi*t)
            center = shoulder_x + 5 * np.sin(np.pi*t)
            grip_sleeve = smooth((radius+u-center)/3) \
                * smooth((radius-u+center)/22) \
                * smooth((v-315)/24) * smooth((520-v)/34)
            coat_y = 399 + (v-350)*.55
            coat_edge = np.interp(coat_y,[380,400,420,440,460,480,500,530],
                                  [85,66,49,41,36,32,34,45])
            coat_x = coat_edge + (u-center+radius)*.86
            grip_coat = sample(source, coat_x, coat_y)
            # The source flank catches more light than the chest. Match its
            # exposure before joining, so the overlap is not a white sticker.
            grip_coat[...,:3] *= np.array([.92,.90,.88])
            hand += grip_coat * grip_sleeve[..., None] * (1 - hand[..., 3:4] / 255)
            hand *= ((u >= 0) & (u < 600) & (v >= 0) & (v < 600))[..., None]
            # Preserve the established pose and silhouette. The detached arm
            # has no chest underneath: accumulated feather masks must not make
            # its interior see-through. Keep the finest outer hairs unchanged.
            coverage = hand[..., 3:4] / 255
            solid = smooth((coverage - .12) / .55)
            repaired_alpha = coverage + (1-coverage)*solid*.92
            hand[..., :3] *= repaired_alpha / np.maximum(coverage, 1e-6)
            hand[..., 3:4] = repaired_alpha * 255
            # Remove only the dark prop remnant at the toe, borrowing nearby
            # fur from the same photographed paw rather than changing anatomy.
            color = hand[..., :3] / np.maximum(repaired_alpha, 1e-6)
            prop = smooth((85-np.max(color, axis=-1))/35) * smooth((v-526)/14)
            nearby = sample(source, sx-32, y-8)
            nearby_color = nearby[..., :3] / np.maximum(nearby[..., 3:4]/255, 1e-6)
            color = color*(1-prop[...,None]) + nearby_color*prop[...,None]
            # Low-radius detail recovery, restricted to opaque arm pixels.
            detail = Image.fromarray(np.clip(color,0,255).astype('uint8'))
            sharpened = np.asarray(detail.filter(ImageFilter.UnsharpMask(radius=.7, percent=45, threshold=3)), dtype=np.float32)
            color += (sharpened-color)*solid
            hand[..., :3] = np.clip(color,0,255)*repaired_alpha
            body = sample(chest_photo, gx, gy) * ((gx >= 0) & (gx < 600))[..., None]
            # Blend textures only INSIDE the opaque torso. Do not draw its old
            # cutout fringe across the new arm: that leaves a white seam.
            joint = smooth((v-350)/95)[...,None]
            interior_body = smooth((body[...,3:4]/255-.90)/.09)
            hand *= 1 - interior_body*(1-joint)
            rgba(hand + body * (1 - hand[..., 3:4] / 255)).save(ASSETS / 'mouse-pose.webp', lossless=True, method=6)
    # Keep the real silhouette when the toes cross the keyboard bezel. The
    # torso is already present in rest.webp; no rectangular chest pixels here.
    rgba(forepaws).crop((0, 396, SIZE, SIZE)).save(ASSETS/'native-forepaws.webp',quality=97,method=6)


if __name__=='__main__':
    build()
