"""Make the product images the page shows: the studio mockups for each garment,
the transparent line-up in the hero, the big logo and the link-preview image.

The mockups are the same ones the skoleklær store (frostlinenorge.no) sells from.
They live in the skole repo, so this reads them from there:

  ~/skole/assets/skole_<garment>_<graa|navy>_<front|back>.jpg   1200 px on white
  ~/skole/assets/skole_<garment>_life.jpg                      on a model
  ~/skole/mockups-ai/<garment>-grey.png                        transparent, for the hero

  python3 _source/make_product_images.py            # writes img/p/ and assets/
  python3 _source/make_product_images.py --skole /path/to/skole

Re-run it when the skole mockups change, then run build.py.
"""
import os, sys
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None
S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
args = sys.argv[1:]
SKOLE = os.path.expanduser(args[args.index('--skole') + 1] if '--skole' in args else '~/skole')
ASSETS = os.path.join(SKOLE, 'assets')
RAW = os.path.join(SKOLE, 'mockups-ai')
OUT = os.path.join(SITE, 'img', 'p')
os.makedirs(OUT, exist_ok=True)

# page id -> skole asset name
GARMENTS = {
    'zip-hoodie': 'ziphoodie',
    'hoodie': 'hoodie',
    'crewneck': 'crewneck',
    'bukse-unisex': 'bukse_unisex',
    'bukse-dame': 'bukse_dame',
}
STAGE_SIZES = (600, 1000)


def save_webp(im, path, q=82, lossless=False):
    im.save(path, 'WEBP', quality=q, method=6, lossless=lossless)
    return os.path.getsize(path)


total = 0
# 1. Studio shots: colour x side, plus the one on a model.
for pid, name in GARMENTS.items():
    shots = [(f'{c}-{v}', f'skole_{name}_{c}_{v}.jpg') for c in ('graa', 'navy') for v in ('front', 'back')]
    shots.append(('life', f'skole_{name}_life.jpg'))
    for tag, fn in shots:
        src = os.path.join(ASSETS, fn)
        if not os.path.exists(src):
            sys.exit(f'missing {src}')
        im = Image.open(src).convert('RGB')
        for w in STAGE_SIZES:
            r = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
            total += save_webp(r, os.path.join(OUT, f'{pid}-{tag}-{w}.webp'), q=82)

# 2. The hero line-up: grey fronts on transparency, trimmed to the garment.
#    The raw PNGs carry a faint alpha haze out to the canvas edge; drop it.
LINEUP = {
    'zip-hoodie': 'ziphoodie-grey.png',
    'hoodie': 'hoodie-grey.png',
    'crewneck': 'crewneck-grey.png',
    'bukse': 'sweatpants-unisex-grey.png',
}
for pid, fn in LINEUP.items():
    im = Image.open(os.path.join(RAW, fn)).convert('RGBA')
    r, g, b, a = im.split()
    a = a.point(lambda v: 0 if v < 40 else v)
    im = Image.merge('RGBA', (r, g, b, a))
    im = im.crop(a.getbbox())
    h = 560
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    total += save_webp(im, os.path.join(OUT, f'lineup-{pid}.webp'), q=86)

# 3. The big logo for the hero, trimmed, white with the grey varsity outline.
logo = Image.open(os.path.join(S, 'brand', 'frostline-logo-outline.png')).convert('RGBA')
logo = logo.crop(logo.getchannel('A').getbbox())
lw = 1800
logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
logo_path = os.path.join(SITE, 'assets', 'frostline-logo-outline.webp')
total += save_webp(logo, logo_path, lossless=True)
print('hero logo', logo.size)

# 4. Link preview (WhatsApp, Snapchat, iMessage): logo over the line-up.
W, H = 1200, 630
og = Image.new('RGB', (W, H), (11, 11, 13))
glow = Image.new('L', (W, H), 0)
gp = glow.load()
for y in range(H):
    for x in range(0, W, 2):
        d = ((x - W / 2) / (W * .55)) ** 2 + ((y - H * .42) / (H * .7)) ** 2
        v = max(0, int(26 * (1 - d)))
        gp[x, y] = v
        if x + 1 < W:
            gp[x + 1, y] = v
og.paste((255, 255, 255), (0, 0), glow)
lg = logo.resize((840, round(logo.height * 840 / logo.width)), Image.LANCZOS)
og.paste(lg, ((W - lg.width) // 2, 70), lg)
items = [Image.open(os.path.join(OUT, f'lineup-{p}.webp')) for p in LINEUP]
ih = 330
items = [i.resize((round(i.width * ih / i.height), ih), Image.LANCZOS) for i in items]
gap = 34
row = sum(i.width for i in items) + gap * (len(items) - 1)
x = (W - row) // 2
for i in items:
    og.paste(i, (x, H - ih - 44), i)
    x += i.width + gap
og.save(os.path.join(SITE, 'assets', 'og.jpg'), quality=86, optimize=True, progressive=True)

n = len([f for f in os.listdir(OUT) if f.endswith('.webp')])
print(f'{n} files in img/p, {round(total / 1e6, 1)} MB written, og.jpg done')
