"""Fit the clean reference portrait to the existing desk poses."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/assets/cream-kitten'


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def match_shoulder_edges(result):
    # Continue the chest coat around each marked flank. Work from a broad area
    # of opaque fur so the new shoulder has volume all the way to the armpit.
    scale = 1.5
    bleed = result.shape[1] / scale - 600
    contours = [
        (1, 95, [314, 340, 370, 402, 432, 465, 502, 551], [0, 5, 17, 28, 30, 24, 10, 0]),
        (-1, 457, [370, 398, 427, 458, 482, 513, 554], [0, 4, 9, 15, 16, 8, 0]),
    ]
    for inward, edge_x, rows, extension in contours:
        x0 = round((edge_x + bleed - 146) * scale)
        x1 = round((edge_x + bleed + 146) * scale)
        y0, y1 = round(rows[0] * scale), round(rows[-1] * scale)
        patch = result[y0:y1, x0:x1].copy()
        yy, xx = np.indices(patch.shape[:2], dtype=np.float32)
        y = (yy + y0) / scale
        distance = inward * ((xx + x0) / scale - bleed - edge_x)
        spread = PchipInterpolator(rows, extension)(y)
        offset = spread * (1 - smooth((distance + spread) / 135))
        sx = xx + inward * scale * offset
        fur = np.asarray(Image.fromarray(patch).convert('RGBa'), dtype=np.float32)
        def sample_at(x):
            return np.stack([map_coordinates(ch, [yy, x], order=1, mode='nearest')
                             for ch in fur.transpose(2, 0, 1)], axis=-1)
        shape = sample_at(sx)
        # Sample the color beneath the traced silhouette, retaining its own
        # alpha and whisker detail. Fade back into the native chest texture.
        coat = sample_at(sx + inward * scale * 18)
        edge_tint = smooth(spread / 12) * (1 - smooth((distance + spread) / 66))
        amount = (.72 * edge_tint[..., None]) * smooth((coat[..., 3:4] - 222) / 33)
        pigment = coat[..., :3] * shape[..., 3:] / np.maximum(coat[..., 3:], 1)
        shape[..., :3] += amount * (pigment - shape[..., :3])
        out = Image.fromarray(shape.clip(0,255).round().astype('uint8'), 'RGBa').convert('RGBA')
        changed = offset > .001
        result[y0:y1, x0:x1][changed] = np.asarray(out)[changed]


def build():
    # This transparent master is the left portrait in the alignment sheet.
    # Interpolate premultiplied fur edges along with the face and headset.
    head = np.asarray(Image.open(ASSETS / 'reference-body.webp').convert('RGBa'), dtype=np.float32)

    for name in ('rest', 'grip', 'burst'):
        plate = Image.open(ASSETS / f'upright-{name}.webp').convert('RGBA')
        result = np.array(plate)
        # Work only above the shoulders. All dimensions here are portrait units.
        h = 620
        py, px = (np.indices((h, plate.width), dtype=np.float32) + .5) / 1.5 - .5
        px -= plate.width / 1.5 - 600
        rows = np.arange(-100, 602)
        desk_y = rows + 48*(1-smooth((rows-330)/270)) - 24*(1-smooth((rows-320)/110))
        y = np.interp(py, desk_y, rows)
        angle = np.deg2rad(12) * (1-smooth((y-315)/180))
        sx = 265 + (px-265)*np.cos(angle) - (y-470)*np.sin(angle)
        sy = 470 + (px-265)*np.sin(angle) + (y-470)*np.cos(angle)
        # Register the reference by translation at the chin. Blend into the
        # desk pose only below the face, using its existing neck coordinates.
        neck = smooth((y - 315) / 67)
        tx = (1 - neck) * (px + 33) + neck * sx
        ty = (1 - neck) * (y + 1) + neck * sy
        coords = [(ty+.5)*2-.5, (tx+.5)*2-.5]
        new = np.stack([map_coordinates(ch, coords, order=1) for ch in head.transpose(2,0,1)], axis=-1)
        weight = 1-smooth((py-341)/63)
        if name == 'burst':
            # Keep the original foreground of the typing animation in front of the cheek.
            weight *= 1-smooth((sy-224)/16)*smooth((261-sx)/15)*smooth((sx-129)/18)
        old = np.asarray(plate.convert('RGBa'))[:h]
        mixed = old + (new-old)*weight[...,None]
        patch = np.array(Image.fromarray(np.clip(mixed,0,255).round().astype('uint8'), 'RGBa').convert('RGBA'))
        changed = weight > 0
        result[:h][changed] = patch[changed]
        if name == 'rest':
            match_shoulder_edges(result)
        Image.fromarray(result).save(ASSETS / f'reference-head-{name}.webp', lossless=True, method=4)


if __name__ == '__main__':
    build()
