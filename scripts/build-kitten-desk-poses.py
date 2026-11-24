"""Build desk poses in one upright portrait coordinate system (600 units high)."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/assets/cream-kitten'
MASTERS = ROOT / 'scripts/assets/cream-kitten'
SCALE = 1.5
LEFT_MARGIN = 100


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def sample(path, x, y, scale, left_margin=0):
    # Interpolate premultiplied fur pixels to avoid a dark line on light desks.
    data = np.asarray(Image.open(path).convert('RGBa'))
    coords = [(y + .5) * scale - .5, (x + left_margin + .5) * scale - .5]
    return np.stack([map_coordinates(channel, coords, order=1, mode='constant')
                     for channel in data.transpose(2, 0, 1)], axis=-1)


def save(name, data):
    image = Image.fromarray(data.astype('uint8'), 'RGBa').convert('RGBA')
    image.save(ASSETS / name, quality=95, method=6, alpha_quality=100)


def build_keyboard_leg():
    # Turn the continuous foreleg into local limb coordinates for key presses.
    y, x = (np.indices((405, 270), dtype=np.float32) + .5) / SCALE - .5
    angle = np.arctan2(135, 153)
    c, s = np.cos(angle), np.sin(angle)
    sx = 96 + (x - 90) * c - (y - 32) * s
    sy = 426 + (x - 90) * s + (y - 32) * c
    leg = sample(MASTERS / 'mouse-pose-master.webp', sx, sy, SCALE, 200)
    # Feather into the shoulder only. Follow the inner elbow to remove the
    # adjacent chest visible in this crop, retaining the opaque wrist and toes.
    inner = np.interp(y, [0, 55, 105, 135, 155, 175, 270], [150, 151, 138, 126, 125, 145, 150])
    edge = 2 + 6 * (1 - smooth((y - 60) / 85))
    # Round the top so the opaque coat starts under the chest. The outermost
    # hairs keep their photographed alpha along both sides of the foreleg.
    cap = 6 + 24 * ((x - 84) / 62) ** 2
    matte = smooth((y - cap) / 14) * smooth((inner - x) / edge)
    coat_weight = (1 - smooth((y - 42) / 86))[..., None]
    for side, body_x, body_y, direction in [('left', 153, 365, 1), ('right', 404, 433, -1)]:
        coat = sample(ASSETS / 'reference-body.webp',
                      body_x + direction * (x - 82) * .45, body_y + (y - 38) * .52, 2)
        # Mix the actual side's fur and lighting in straight color, then apply
        # the existing silhouette. Restrict the blend to opaque chest samples.
        weight = .84 * coat_weight * smooth((coat[..., 3:4].astype(float) - 235) / 20)
        rgb = leg[..., :3] * (1 - weight) + coat[..., :3] * (leg[..., 3:4] / 255) * weight
        colored = np.concatenate([rgb, leg[..., 3:4]], axis=2)
        # Bake the elbow curve into continuous fur to avoid subpixel strip seams.
        # Leave 24 units of bleed on the outside of the limb.
        rows, cols = np.indices((leg.shape[0], round(204*SCALE)), dtype=np.float32)
        t = np.clip((rows+.5) / (155*SCALE), 0, 1)
        bow = (-10 / .78) * 16*t*t*(1-t)*(1-t)
        coords = [rows, cols - (24 + bow)*SCALE]
        pixels = colored * matte[..., None]
        curved = np.stack([map_coordinates(ch, coords, order=1) for ch in pixels.transpose(2,0,1)], axis=-1)
        save(f'key-leg-{side}.webp', np.rint(curved))


def build():
    build_keyboard_leg()
    y, x = (np.indices((900, 1050), dtype=np.float32) + .5) / SCALE - .5
    x -= LEFT_MARGIN
    # Keep the base and toe landmarks fixed while shortening the chest.
    rows = np.arange(-100, 602)
    chest_rows = rows + 48 * (1 - smooth((rows - 330) / 270))
    # Lift the head as a whole, easing the displacement to zero at the shoulders.
    # Sample from the master once so the fine fur follows the new neckline.
    head_lift = 24 * (1 - smooth((rows - 320) / 110))
    y = np.interp(y, chest_rows - head_lift, rows)
    # Rigid correction through the eyes and ears, tapering into the shoulders.
    angle = np.deg2rad(12) * (1 - smooth((y - 315) / 180))
    dx, dy = x - 265, y - 470
    sx = 265 + dx * np.cos(angle) - dy * np.sin(angle)
    sy = 470 + dx * np.sin(angle) + dy * np.cos(angle)
    rest = sample(ASSETS / 'reference-body.webp', sx, sy, 2)
    save('upright-rest.webp', rest)
    grip = sample(MASTERS / 'mouse-pose-master.webp', sx, sy, SCALE, 200)
    # The master has a continuous shoulder and foreleg. Blend only inside the
    # chest where the photographic plates overlap, before runtime compositing.
    mix = smooth((sy - 320) / 75) * (1 - smooth((sx - 145) / 135))
    plate = np.rint(rest + (grip.astype(float) - rest) * mix[..., None])
    # Translate the toe rigidly into the extra left bleed,
    # distributing the reach over the forearm and fading it out at the chest.
    extension_px = round(38 * SCALE)
    gy, gx = np.indices((plate.shape[0], plate.shape[1] + extension_px), dtype=np.float32)
    gx -= extension_px
    reach = smooth((gy / SCALE - 375) / 110) * (1 - smooth((gx / SCALE - 35) / 180))
    coords = [gy, gx + extension_px * reach]
    extended = np.stack([map_coordinates(ch, coords, order=1) for ch in plate.transpose(2, 0, 1)], axis=-1)
    save('upright-grip.webp', extended)
    save('upright-burst.webp', sample(ASSETS / 'portrait.webp', sx, sy, 1000 / 600))


if __name__ == '__main__':
    build()
