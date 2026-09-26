"""The groups' own chest logos for the ticker under style b's hero.

  python3 _source/make_logos.py

Reads _source/logo-src/<post>.png (gitignored: print files, up to 37 MB each) and writes
img/logo/<post>.webp, trimmed to the ink and sized for the ticker at twice its height on a
wide screen. The number is the group's post in groups.json, so the ticker runs in the
same order as the group photos.

Where each original came from is in _source/logos.json: the zip hoodie's front chest print
from that group's order in the print system (s3://ftmerch-eu-north-1), except Czarface
(its November 2025 order predates the print system) and Glitch (no zip in their order,
so the hoodie back wordmark). A group without a file is left out of the ticker.
"""
import glob, os
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
OUT = os.path.join(SITE, 'img', 'logo')
os.makedirs(OUT, exist_ok=True)


def factor(aspect):
    """Height relative to the ticker's base height, so a wide wordmark and a square crest
    carry about the same weight: equal area, within limits."""
    return max(.62, min(1.5, (3.5 / aspect) ** .5))


for f in sorted(glob.glob(os.path.join(S, 'logo-src', '*.png'))):
    n = os.path.basename(f)[:-4]
    im = Image.open(f).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 10 else 0).getbbox()
    im = im.crop(box)
    h = round(2 * 64 * factor(im.width / im.height))
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    im.save(os.path.join(OUT, f'{n}.webp'), 'WEBP', quality=78, method=6)
    print(n, im.size, f'{os.path.getsize(os.path.join(OUT, n + ".webp")) // 1024} KB')
