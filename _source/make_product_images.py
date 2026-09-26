"""Make the product images the page shows: one on-model photo per garment (two for the
cuts of the trousers and shorts), and the link-preview image.

The photos come from two places, all in the same look (one model, light grey studio):
  ~/skole/assets/skole_<garment>_life.jpg   the skoleklær store's shots, where they fit
  _source/model-photos/<id>.png             made by model_photos.mjs where they did not
                                            (hoodie and zip with russ-length cords, and
                                            the garments the school store does not sell)

  python3 _source/make_product_images.py            # writes img/p/ and assets/og.jpg
  python3 _source/make_product_images.py --skole /path/to/skole

Re-run it when a photo changes, then run build.py.
"""
import os, sys
from PIL import Image, ImageOps

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
args = sys.argv[1:]
SKOLE = os.path.expanduser(args[args.index('--skole') + 1] if '--skole' in args else '~/skole')
GEN = os.path.join(S, 'model-photos')
OUT = os.path.join(SITE, 'img', 'p')
os.makedirs(OUT, exist_ok=True)

# image id (as products.json names it) -> source photo
PHOTOS = {
    'zip-hoodie': f'{GEN}/zip-hoodie.png',
    'hoodie': f'{GEN}/hoodie.png',
    'crewneck': f'{SKOLE}/assets/skole_crewneck_life.jpg',
    'collegejakke': f'{GEN}/collegejakke.png',
    'bukse-unisex': f'{SKOLE}/assets/skole_bukse_unisex_life.jpg',
    'bukse-dame': f'{SKOLE}/assets/skole_bukse_dame_life.jpg',
    'shorts-unisex': f'{GEN}/shorts-unisex.png',
    'shorts-dame': f'{GEN}/shorts-dame.png',
    't-skjorte': f'{SKOLE}/assets/skole_tshirt_life.jpg',
    'longsleeve': f'{SKOLE}/assets/skole_longsleeve_life.jpg',
    'singlet': f'{GEN}/singlet.png',
}
SIZES = (600, 1000)

missing = [p for p in PHOTOS.values() if not os.path.exists(p)]
if missing:
    sys.exit('missing:\n  ' + '\n  '.join(missing))

total = 0
for pid, src in PHOTOS.items():
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    side = min(im.size)
    im = ImageOps.fit(im, (side, side), Image.LANCZOS)
    for w in SIZES:
        out = os.path.join(OUT, f'{pid}-model-{w}.webp')
        im.resize((w, w), Image.LANCZOS).save(out, 'WEBP', quality=84, method=6)
        total += os.path.getsize(out)

# Link preview (WhatsApp, Snapchat, iMessage): the logo over five of the garments.
logo = Image.open(os.path.join(SITE, 'assets', 'frostline-logo-outline.webp')).convert('RGBA')
W, H = 1200, 630
og = Image.new('RGB', (W, H), (9, 9, 11))
lg = logo.resize((760, round(logo.height * 760 / logo.width)), Image.LANCZOS)
og.paste(lg, ((W - lg.width) // 2, 52), lg)
picks = ['zip-hoodie', 'hoodie', 'collegejakke', 'crewneck', 'bukse-unisex']
tw, gap = 212, 12
th = 390
x = (W - (tw * len(picks) + gap * (len(picks) - 1))) // 2
for p in picks:
    t = ImageOps.fit(Image.open(os.path.join(OUT, f'{p}-model-1000.webp')).convert('RGB'), (tw, th), Image.LANCZOS, centering=(.5, .45))
    og.paste(t, (x, H - th - 46))
    x += tw + gap
og.save(os.path.join(SITE, 'assets', 'og.jpg'), quality=86, optimize=True, progressive=True)

print(f'{len(PHOTOS)} photos -> img/p ({round(total / 1e6, 1)} MB), og.jpg done')
