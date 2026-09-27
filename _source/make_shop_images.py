"""The product photos on the garment cards and the product pages: every garment cut out of
its white studio ground (transparent webp, so it floats on the dark cards), square, front
(and back where there is one), in each colour it is shown in.

  python3 _source/make_shop_images.py            # writes img/shop/ and _source/shop.json
  python3 _source/make_shop_images.py --skole /path/to/skole

Where they come from:
  ~/skole/assets/skole_<x>_<front|back>.jpg   the skoleklær store's studio shots (grey, navy, white)
  black                                       made here from the navy shot: its grey levels, a
                                              little darker, so the cords and the light stay
  _source/product-shots/<name>.png            shorts, singlet and college jacket (product_shots.mjs),
                                              re-framed here to sit like the skole shots

The cut: the ground is pure white (255) and the garments are not (the skole store pulls its
white garments to 240 on purpose, the ash grey and the generated shots sit below 247 too),
so every near-white region that touches the edge of the frame is ground. A near-white island
inside the garment stays unless it is big and pure white (a gap between arm and body seen
through to the ground); the white cords are shaded and never pure. The edge is pulled in a
pixel and softened so no white rim shows on black.

Also writes <first front>-og.jpg per garment: the cutout on the cards' dark ground, for the
link preview (apps show a transparent preview on white or black at random).

shop.json tells build.py what exists: per garment its cuts, per cut its colours, per colour
the image names. Colour names and swatches are in COLOURS. Re-run it when a photo changes,
then run build.py.
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw
from scipy import ndimage

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
args = sys.argv[1:]
SKOLE = os.path.expanduser(args[args.index('--skole') + 1] if '--skole' in args else '~/skole')
GEN = os.path.join(S, 'product-shots')
OUT = os.path.join(SITE, 'img', 'shop')
SIZES = (600, 1200)
os.makedirs(OUT, exist_ok=True)

# colour key -> the name shown, the swatch, and whether a name on the back is printed white
COLOURS = {
    'gra': {'name': 'Grå', 'hex': '#d3d3d6', 'dark': False},
    'navy': {'name': 'Navy', 'hex': '#1f2745', 'dark': True},
    'svart': {'name': 'Svart', 'hex': '#141416', 'dark': True},
    'hvit': {'name': 'Hvit', 'hex': '#ffffff', 'dark': False},
}


def skole(x):
    return ('skole', f'{SKOLE}/assets/skole_{x}.jpg')


def black(x):
    return ('black', f'{SKOLE}/assets/skole_{x}.jpg')


def gen(name, fill):
    """fill: (largest width, largest height) the garment may take of the square, as the skole
    shots do (hoodies about .76 x .95, trousers .40 x .96)."""
    return ('gen', f'{GEN}/{name}.png', fill)


def fleece(g):
    """Grey and navy from the skole store, black made from the navy."""
    return {
        'gra': {'front': skole(f'{g}_graa_front'), 'back': skole(f'{g}_graa_back')},
        'navy': {'front': skole(f'{g}_navy_front'), 'back': skole(f'{g}_navy_back')},
        'svart': {'front': black(f'{g}_navy_front'), 'back': black(f'{g}_navy_back')},
    }


# garment id (products.json) -> cut ('' when it has one) -> colour -> view -> source
SOURCES = {
    'zip-hoodie': {'': fleece('ziphoodie')},
    'hoodie': {'': fleece('hoodie')},
    'crewneck': {'': fleece('crewneck')},
    'bukse': {'unisex': fleece('bukse_unisex'), 'dame': fleece('bukse_dame')},
    'shorts': {'unisex': {'gra': {'front': gen('shorts-unisex', (.70, .80))}},
               'dame': {'gra': {'front': gen('shorts-dame', (.66, .70))}}},
    't-skjorte': {'': {'hvit': {'front': skole('tshirt_hvit_front'), 'back': skole('tshirt_hvit_back')}}},
    'longsleeve': {'': {'hvit': {'front': skole('longsleeve_hvit_front'), 'back': skole('longsleeve_hvit_back')}}},
    'singlet': {'': {'hvit': {'front': gen('singlet', (.70, .92))}}},
    'collegejakke': {'': {'navy': {'front': gen('collegejakke', (.84, .94))}}},
}


GROUND = 250  # min channel at or above this is white ground (or a pure white gap)
CARD = (18, 18, 22)  # the cards' dark ground, for the link-preview jpg


def cutout(im):
    """The garment with the white ground made transparent."""
    a = np.asarray(im.convert('RGB'))
    lo = a.min(axis=2)
    lab, n = ndimage.label(lo >= GROUND)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    ground = np.isin(lab, list(edge))
    for k in set(range(1, n + 1)) - edge:  # islands: a gap seen through to the ground, or a highlight
        m = lab == k
        if m.sum() > 2500 and np.median(lo[m]) >= 254:
            ground |= m
    alpha = Image.fromarray(np.where(ground, 0, 255).astype(np.uint8), 'L')
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.8))
    out = im.convert('RGBA')
    out.putalpha(alpha)
    return out


def preview(cut):
    """The cutout on the dark card ground under a soft light, as the cards show it."""
    n = cut.width
    bg = Image.new('RGBA', (n, n), CARD + (255,))
    g = Image.new('L', (n, n), 0)
    ImageDraw.Draw(g).ellipse((n * .12, n * .1, n * .88, n * .9), fill=42)
    light = Image.new('RGBA', (n, n), (255, 255, 255, 0))
    light.putalpha(g.filter(ImageFilter.GaussianBlur(n * .14)))
    bg.alpha_composite(light)
    bg.alpha_composite(cut)
    return bg.convert('RGB')


def load(src):
    kind, path = src[0], src[1]
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    if kind == 'skole':
        return im
    if kind == 'black':
        a = np.asarray(im).astype(np.float32) / 255
        L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        t = np.clip((L - .35) / .15, 0, 1)  # the fabric gets darker, the cords and the white stay
        out = L * .78 * (1 - t) + L * t
        return Image.fromarray((np.clip(np.stack([out] * 3, -1), 0, 1) * 255).astype(np.uint8))
    # a generated shot: find the garment, scale it to the fill it may take, centre it on white
    fw, fh = src[2]
    a = np.asarray(im)
    ys, xs = np.where(a.min(axis=2) < 240)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    g = im.crop(box)
    n = 1200
    s = min(fw * n / g.width, fh * n / g.height)
    g = g.resize((round(g.width * s), round(g.height * s)), Image.LANCZOS)
    c = Image.new('RGB', (n, n), (255, 255, 255))
    c.paste(g, ((n - g.width) // 2, (n - g.height) // 2))
    return c


missing = sorted({v[1] for cuts in SOURCES.values() for cols in cuts.values() for views in cols.values()
                  for v in views.values() if not os.path.exists(v[1])})
if missing:
    sys.exit('missing:\n  ' + '\n  '.join(missing))

manifest, total, n_img = {}, 0, 0
for gid, cuts in SOURCES.items():
    manifest[gid] = []
    for cut, cols in cuts.items():
        entry = {'cut': cut, 'colours': []}
        for ck, views in cols.items():
            names = {}
            for view, src in views.items():
                name = '-'.join(x for x in (gid, cut, ck, view) if x)
                im = load(src)
                if im.size != (1200, 1200):
                    im = ImageOps.fit(im, (1200, 1200), Image.LANCZOS)
                im = cutout(im)
                for w in SIZES:
                    out = os.path.join(OUT, f'{name}-{w}.webp')
                    (im if w == 1200 else im.resize((w, w), Image.LANCZOS)).save(out, 'WEBP', quality=86, method=6)
                    total += os.path.getsize(out)
                if not manifest[gid] and not entry['colours'] and view == 'front':
                    preview(im).save(os.path.join(OUT, f'{name}-og.jpg'), quality=86, optimize=True, progressive=True)
                names[view] = name
                n_img += 1
            entry['colours'].append({'k': ck, **names})
        manifest[gid].append(entry)

json.dump({'_note': 'Written by make_shop_images.py; do not edit.', 'colours': COLOURS, 'garments': manifest},
          open(os.path.join(S, 'shop.json'), 'w'), ensure_ascii=False, indent=1)
print(f'{n_img} photos, {n_img * len(SIZES)} files, {total / 1e6:.1f} MB -> img/shop/, shop.json')
