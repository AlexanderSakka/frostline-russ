"""The product photos on the garment cards and the product pages: every garment cut out of
its white studio ground (transparent webp, so it floats on the dark cards), square, front
(and back where there is one), in each colour it is shown in.

  python3 _source/make_shop_images.py            # writes img/shop/ and _source/shop.json
  python3 _source/make_shop_images.py --skole /path/to/skole

Where they come from:
  ~/skole/assets/skole_<x>_<front|back>.jpg   the skoleklær store's studio shots (grey, navy, white)
  _source/product-shots/<name>.png            shorts, singlet and college jacket (product_shots.mjs),
                                              re-framed here to sit like the skole shots

The cut is a known-background matte, since every photo is a garment on pure white. The
ground is the near-white (249-255) that touches the frame's edge and lies within 4 px of pure
white (253-255), where JPEG noise and the generated shots' faint haze sit. On a white garment
(t-skjorte, longsleeve, singlet) the brightest fabric is 246-250 itself, so there only
253-255 counts, or the ground creeps into the shoulder. Within 3.5 px of it, a pixel is part garment and part white, and how much of each
follows from how far it is from white against the garment colour beside it; it then takes
that garment colour, so no white rim is left to show on the dark cards. Two more kinds of
ground: a thin white slit between sleeve and body that is closed at both ends (a pure white
island at most 6 px wide, near the outline, in dark fabric), and the narrow end of such a
slit (a line lighter than both its sides, joined to the ground). The white cords and the
jacket's cuff stripes are neither: they are wide, and they sit away from the outline.

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

# colour key -> the name shown, the swatch, and whether a name on the back is printed white.
# Only colours Frostline sells: no black of any garment (Alexander, 2026-09-27).
COLOURS = {
    'gra': {'name': 'Grå', 'hex': '#d3d3d6', 'dark': False},
    'navy': {'name': 'Navy', 'hex': '#1f2745', 'dark': True},
    'hvit': {'name': 'Hvit', 'hex': '#ffffff', 'dark': False},
}


def skole(x):
    return ('skole', f'{SKOLE}/assets/skole_{x}.jpg')


def gen(name, fill):
    """fill: (largest width, largest height) the garment may take of the square, as the skole
    shots do (hoodies about .76 x .95, trousers .40 x .96)."""
    return ('gen', f'{GEN}/{name}.png', fill)


def fleece(g):
    """Grey and navy, from the skole store."""
    return {
        'gra': {'front': skole(f'{g}_graa_front'), 'back': skole(f'{g}_graa_back')},
        'navy': {'front': skole(f'{g}_navy_front'), 'back': skole(f'{g}_navy_back')},
    }


# garment id (products.json) -> cut ('' when it has one) -> colour -> view -> source
SOURCES = {
    'zip-hoodie': {'': fleece('ziphoodie')},
    'hoodie': {'': fleece('hoodie')},
    'crewneck': {'': fleece('crewneck')},
    'bukse': {'unisex': fleece('bukse_unisex'), 'dame': fleece('bukse_dame')},
    'shorts': {'unisex': {'gra': {'front': gen('shorts-unisex', (.70, .80))},
                          'navy': {'front': gen('shorts-unisex-navy', (.70, .80))}},
               'dame': {'gra': {'front': gen('shorts-dame', (.66, .70))},
                        'navy': {'front': gen('shorts-dame-navy', (.66, .70))}}},
    't-skjorte': {'': {'hvit': {'front': skole('tshirt_hvit_front'), 'back': skole('tshirt_hvit_back')}}},
    'longsleeve': {'': {'hvit': {'front': skole('longsleeve_hvit_front'), 'back': skole('longsleeve_hvit_back')}}},
    'singlet': {'': {'hvit': {'front': gen('singlet', (.70, .92))}}},
    'collegejakke': {'': {'navy': {'front': gen('collegejakke', (.84, .94))}}},
}


CARD = (18, 18, 22)  # the cards' dark ground, for the link-preview jpg


def _shift(a, dy, dx):
    p = np.pad(a, ((abs(dy), abs(dy)), (abs(dx), abs(dx))), mode='edge')
    h, w = a.shape
    return p[abs(dy) + dy: abs(dy) + dy + h, abs(dx) + dx: abs(dx) + dx + w]


def cutout(im, band=3.5):
    """The garment with its white ground made transparent (see the top of this file)."""
    rgb = np.asarray(im.convert('RGB')).astype(np.float32)
    d = 255 - rgb.min(axis=2)  # darkness: 0 is the white ground
    # how far from 255 still counts as ground: a white garment's fabric reaches 246-250, so
    # there only 253-255 is ground (a light rim cannot show on white anyway)
    ground_d = 2 if np.median(d[d > 6]) < 25 else 6
    lab, n = ndimage.label(d <= ground_d)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    # ...but only near pure white: the ground's near-white is JPEG noise beside 253-255 pixels,
    # while a white garment's brightest fabric (245-250) has none, so the fill stops at it
    pure = ndimage.distance_transform_edt(d > 2) <= 4
    G = np.isin(lab, list(edge)) & pure
    near = ndimage.distance_transform_edt(~G) <= 25
    for i in set(range(1, n + 1)) - edge:  # a slit closed at both ends
        m = lab == i
        if (m & near).any() and ndimage.distance_transform_edt(m).max() <= 3:
            ring = ndimage.binary_dilation(m, iterations=6) & ~ndimage.binary_dilation(m, iterations=2)
            if np.median(d[ring]) >= 60:
                G |= m
    R = np.zeros_like(G)  # lighter than both sides 3 px away: the narrow end of a slit
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a1, a2 = _shift(d, 3 * dy, 3 * dx), _shift(d, -3 * dy, -3 * dx)
        R |= (d < .72 * a1) & (d < .72 * a2) & (np.minimum(a1, a2) >= 45)
    dist = ndimage.distance_transform_edt(~G)
    B = (dist <= band) & ~G
    lab2, _ = ndimage.label(R | B | G)
    M = R & np.isin(lab2, list(set(np.unique(lab2[G])) - {0}))
    U = B | (ndimage.binary_dilation(M) & ~G)  # part garment, part white
    # near-white a little further in (a generated shot's hazy gap between the legs): judged
    # against the nearest solid pixel too, which is the fabric beside it; a cord or a white
    # garment is its own nearest solid pixel, so it stays
    U |= (dist <= 6) & (d < 40) & ~G
    S = ~G & ~U                                 # all garment
    # a few pixels of "garment" on their own, floating in a gap, are haze: ground
    lab3, n3 = ndimage.label(S, structure=np.ones((3, 3)))
    if n3 > 1:
        size = np.bincount(lab3.ravel())
        specks = np.isin(lab3, np.where(size < 60)[0]) & (lab3 > 0)
        G |= specks
        S &= ~specks
    _, (iy, ix) = ndimage.distance_transform_edt(~S, return_indices=True)
    F = rgb[iy, ix]                             # the garment colour beside each pixel
    k = (255 - F).argmax(axis=2)[..., None]
    span = np.take_along_axis(255 - F, k, 2)[..., 0]
    cov = np.clip(np.take_along_axis(255 - rgb, k, 2)[..., 0] / np.maximum(span, 1), 0, 1)
    # a white garment is too close to white to measure against: fade by distance instead
    a_u = np.where(span >= 25, cov, np.clip(dist / band, 0, 1))
    alpha = ndimage.gaussian_filter(np.where(G, 0, np.where(U, a_u, 1)).astype(np.float32), .5)
    alpha[S & (ndimage.distance_transform_edt(S) > 2)] = 1
    out = np.where(U[..., None], F, rgb)
    return Image.fromarray(np.dstack([np.clip(out, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8), 'RGBA')


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
