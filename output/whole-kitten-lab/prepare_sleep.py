"""Prepare the full sleeping kitten: python prepare_sleep.py CLOSED_PORTRAIT.png"""
from pathlib import Path
import sys
from PIL import Image

lab = Path(__file__).resolve().parent
assets = lab.parents[1] / 'src/assets/cream-kitten'
with Image.open(assets/'rest-photo.webp') as rest, Image.open(sys.argv[1]) as closed:
    if closed.width * rest.height != closed.height * rest.width:
        raise ValueError('Expected the same framing as the resting kitten')
    portrait = closed.convert('RGB').resize(rest.size, Image.Resampling.LANCZOS)
    # Only reuse the silhouette; all visible colors come from the closed portrait.
    portrait.putalpha(rest.getchannel('A'))
    portrait.save(assets/'sleep-photo.webp', lossless=True, method=4)
