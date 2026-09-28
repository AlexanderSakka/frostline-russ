"""Shorter drawcords on the hoodie and zip hoodie photos, without drawing them again.

  python3 _source/shorten_cords.py          # writes _source/product-shots/cords/*.png and model-photos/hoodie.png

Alexander found the cords too long on the skole store's product shots (both colours of both
hoodies) and on the hoodie model photo (2026-09-28); the zip hoodie model photo, with its cords
ending on the upper chest, was right. So every cord here is brought up to the same share of
the garment as on that photo: CORD_SHARE of the way from where the cord leaves the hood to the
hem. Nothing else in the photo moves: the cord's own cut end (the last few px of tape and the
little shadow under it) is lifted to the new height, and the fabric where the rest of the cord
hung is filled in from the fabric just beside it, which on a flat front is the same fabric.

The skole store's files are left alone (the school garments keep their cords); the edited
copies go to _source/product-shots/cords/ (gitignored), which make_shop_images.py reads.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage, sparse
from scipy.sparse.linalg import spsolve

S = os.path.dirname(os.path.abspath(__file__))
SKOLE = os.path.expanduser('~/skole')
OUT = os.path.join(S, 'product-shots', 'cords')
CORD_SHARE = .27  # the zip hoodie model photo of 2026-09-28: cord length / (hem - cord top)

# photo -> where it goes, and the hem row (the garment's lowest row at the front, in px)
JOBS = [
    (f'{SKOLE}/assets/skole_ziphoodie_graa_front.jpg', f'{OUT}/ziphoodie_graa_front.png', None),
    (f'{SKOLE}/assets/skole_ziphoodie_navy_front.jpg', f'{OUT}/ziphoodie_navy_front.png', None),
    (f'{SKOLE}/assets/skole_hoodie_graa_front.jpg', f'{OUT}/hoodie_graa_front.png', None),
    (f'{SKOLE}/assets/skole_hoodie_navy_front.jpg', f'{OUT}/hoodie_navy_front.png', None),
    # the model photo: the same model and framing as the zip hoodie one, so the same end row
    (f'{S}/model-refs/hoodie-2026-09-28-ai.png', f'{S}/model-photos/hoodie.png', 'end:520'),
]


def cords(a):
    """The two hanging cords: tall, narrow, much lighter than the fabric around them."""
    lo = a.min(axis=2)
    h, w = lo.shape
    fab = float(np.median(lo[int(h * .55):int(h * .65), int(w * .3):int(w * .4)]))
    m = lo > fab + .45 * (255 - fab)
    m[:int(h * .05)] = False
    m[:, :int(w * .25)] = False
    m[:, int(w * .75):] = False
    m[int(h * .6):] = False  # the joggers' cords on a model photo hang lower
    lab, n = ndimage.label(m)
    out = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if ys.max() - ys.min() > h * .08 and xs.max() - xs.min() < w * .06:
            out.append((xs.min(), ys.min(), xs.max(), ys.max()))
    return sorted(out)


def hem(a):
    """The garment's lowest row near the centre: the last row that is not white ground."""
    lo = a.min(axis=2)
    col = lo[:, a.shape[1] // 2 - 40: a.shape[1] // 2 + 40].min(axis=1)
    return int(np.where(col < 245)[0].max())


def blend(dst, src, y0, x0, open_top=False):
    """Put src (h x w x 3) into dst at (y0, x0) seamlessly: src keeps its texture, and a smooth
    correction (the harmonic function that matches dst on the border) takes away any step in
    brightness, so the patch leaves no rectangle behind (Poisson image editing). open_top: the
    top border is not matched (it runs through the white cord, which would glow down into
    the fabric)."""
    h, w = src.shape[:2]
    out = dst.copy()
    n = h * w
    idx = np.arange(n).reshape(h, w)
    rows, cols, vals = [], [], []
    rhs = np.zeros((n, 3), np.float64)
    ring = dst[y0 - 1:y0 + h + 1, x0 - 1:x0 + w + 1].astype(np.float64)
    for y in range(h):
        for x in range(w):
            i = idx[y, x]
            diag = 4.0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                yy, xx = y + dy, x + dx
                if yy < 0 and open_top:
                    diag -= 1  # no condition on this side
                elif 0 <= yy < h and 0 <= xx < w:
                    rows.append(i); cols.append(idx[yy, xx]); vals.append(-1.0)
                else:  # the border: dst's pixel there, minus what src has at its edge
                    rhs[i] += ring[yy + 1, xx + 1] - src[y, x]
            rows.append(i); cols.append(i); vals.append(diag)
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(n, n))
    corr = np.stack([spsolve(A, rhs[:, c]) for c in range(3)], -1).reshape(h, w, 3)
    out[y0:y0 + h, x0:x0 + w] = src + corr
    return out


def slant(a, cord):
    """How far the cord drifts sideways per row, from a line through its middle over its
    whole length (it can hang a little slanted on a model, and is straight on a flat shot)."""
    x0, y0, x1, y1 = cord
    lo = a[:, :].min(axis=2)
    ys, cs = [], []
    for y in range(y0 + 10, y1 - 6):
        row = lo[y, x0:x1 + 1]
        m = row > (row.max() + np.median(lo[y, x0 - 20:x0 - 8])) / 2
        if m.sum() >= 3:
            ys.append(y); cs.append(x0 + np.where(m)[0].mean())
    return np.polyfit(ys, cs, 1)[0] if len(ys) > 10 else 0.0


def shorten(a, cord, new_end, side):
    """Lift one cord's end from its row to new_end. side: -1 takes fill fabric from the left."""
    x0, y0, x1, y1 = cord
    # margin beside the cord (its shadow too), end piece above the cut, shadow below it; the
    # model photo is 1536 px and its cord casts a longer shadow, so these follow the size
    k = a.shape[0] / 1200
    mx, E, sh = round(10 * k), round(18 * k), round(14 * k)
    lift = y1 - new_end
    if lift <= 0:
        return a
    # 1. fabric over the part that goes, from the fabric just beside it at the same rows
    bx0, bx1 = x0 - mx, x1 + mx + 1
    bw = bx1 - bx0
    ya, yb = new_end - 4, y1 + sh + 1
    sx = bx0 + side * (bw + 6)
    out = blend(a, a[ya:yb, sx:sx + bw], ya, bx0, open_top=True)
    # 2. the cord's own end (tape and the shadow under it), moved up, and sideways as far as
    #    the cord drifts between the two heights
    shift = int(round(-slant(a, cord) * lift))
    pa, pb = y1 - E, y1 + sh + 1
    px0, px1 = x0 - 4, x1 + 5
    out = blend(out, a[pa:pb, px0:px1], pa - lift, px0 + shift)
    return out


os.makedirs(OUT, exist_ok=True)
for src, dst, rule in JOBS:
    if not os.path.exists(src):
        raise SystemExit(f'missing {src}')
    a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    cs = cords(a)
    if len(cs) != 2:
        raise SystemExit(f'{src}: found {len(cs)} cords, expected 2')
    top = min(c[1] for c in cs)
    if rule and rule.startswith('end:'):
        end = int(rule[4:])
    else:
        end = int(top + CORD_SHARE * (hem(a) - top))
    slant_l, slant_r = slant(a, cs[0]), slant(a, cs[1])
    for k, c in enumerate(cs):
        a = shorten(a, c, end, -1 if k == 0 else 1)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst)
    print(f'{os.path.basename(dst)}: cords ended at {cs[0][3]}/{cs[1][3]}, now at {end} (top {top}), '
          f'slant {slant_l:+.3f}/{slant_r:+.3f} px per row')
