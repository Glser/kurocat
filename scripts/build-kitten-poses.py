"""Build identical forepaws from the approved right foreleg.

The source is a lossless crop of the existing right paw. Copying its pixels
keeps the approved paw unchanged; the left uses its horizontal reflection.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/assets/cream-kitten/right-forepaw-master.webp'
TARGET = ROOT / 'src/assets/cream-kitten/native-forepaws.webp'


def build():
    right = Image.open(SOURCE).convert('RGBA')
    assert right.size == (360, 324)
    paws = Image.new('RGBA', (720, 324))
    # Portrait mirror axis x=265: left toe 132, right toe 398.
    # The right crop begins at x=300, so its mirror begins at x=-70.
    paws.paste(ImageOps.mirror(right), (-84, 0))
    paws.paste(right, (360, 0))
    paws.save(TARGET, lossless=True, exact=True, method=6)

    # The original shoulder matte was designed to overlap the chest. When
    # extended over the desk, its broad transparency made the arm look hazy.
    # Normalize that matte across each fur contour, leaving the toes untouched.
    pixels = np.array(right)
    alpha = pixels[:, :, 3].astype(np.float32) / 255
    row_peak = np.maximum(alpha.max(axis=1, keepdims=True), 1 / 255)
    def smooth(value):
        value = np.clip(value, 0, 1)
        return value * value * (3 - 2 * value)
    y = np.arange(right.height)[:, None]
    edge = smooth((alpha / row_peak - 0.06) / 0.58)
    shoulder = smooth((y - 28) / 24)
    forearm = 1 - smooth((y - 166) / 30)
    repaired_alpha = edge * shoulder
    pixels[:, :, 3] = np.round(255 * (alpha + (repaired_alpha - alpha) * forearm))
    # Restore a little local fur contrast without sharpening the alpha edge.
    rgb = np.array(right.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1, percent=90, threshold=3)))
    pixels[:, :, :3] = np.round(pixels[:, :, :3] * (1-forearm[:, :, None]) + rgb * forearm[:, :, None])
    mouse = Image.new('RGBA', paws.size)
    mouse.paste(ImageOps.mirror(Image.fromarray(pixels)), (-84, 0))
    mouse.save(TARGET.with_name('mouse-forepaw.webp'), lossless=True, exact=True, method=6)


if __name__ == '__main__':
    build()
