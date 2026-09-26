"""Turn the Instagram originals in _source/raw/ into the three sizes the page uses:

  img/<post>-<slide>-s.webp   480 px wide   grid tiles and group covers
  img/<post>-<slide>-m.webp   900 px wide   tiles on wide screens
  img/<post>-<slide>-l.webp  1440 px wide   the lightbox

The custom pieces in custom.json get the same three sizes from _source/raw/custom/,
as img/c/<name>-{s,m,l}.webp.

Existing files are kept; pass --force to redo them. When a raw original is missing
(raw/ is gitignored and lives on one Mac), the small size is made from the -m file.

  python3 _source/make_webp.py
"""
import json, os, sys
from PIL import Image, ImageOps

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
IMG = os.path.join(SITE, 'img')
FORCE = '--force' in sys.argv
SIZES = (('s', 480, 78), ('m', 900, 80), ('l', 1440, 84))

# Only posts a card uses: groups.json leaves some out on purpose (Iron Dome, the logo post).
used = set()
for g in json.load(open(os.path.join(S, 'groups.json'))):
    used.add(g['n'])
    used.update(g.get('also', []))

jobs = []  # (base name under img/, raw original)
for p in json.load(open(os.path.join(S, 'posts.json'))):
    if p['n'] not in used:
        continue
    jobs += [(i['file'][:-4], os.path.join(S, 'raw', i['file'])) for i in p['images'] if i['ok']]
for c in json.load(open(os.path.join(S, 'custom.json')))['custom']:
    jobs += [('c/' + f.rsplit('.', 1)[0], os.path.join(S, 'raw', 'custom', f)) for f in c['photos']]
os.makedirs(os.path.join(IMG, 'c'), exist_ok=True)

made = skipped = 0
for base, raw in jobs:
    src = None
    for tag, maxw, q in SIZES:
        out = os.path.join(IMG, f'{base}-{tag}.webp')
        if os.path.exists(out) and not FORCE:
            skipped += 1
            continue
        if src is None:
            if os.path.exists(raw):
                src = ImageOps.exif_transpose(Image.open(raw)).convert('RGB')
            else:
                m = os.path.join(IMG, f'{base}-m.webp')
                if not os.path.exists(m):
                    sys.exit(f'no source for {base}: neither {raw} nor {m}')
                src = Image.open(m).convert('RGB')
        r = src.copy()
        r.thumbnail((maxw, maxw * 2), Image.LANCZOS)
        r.save(out, 'WEBP', quality=q, method=6)
        made += 1
print('written', made, 'kept', skipped)
