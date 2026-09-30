"""Build the site from the JSON files in _source/.

  python3 _source/build.py              # index.html in the live style, plus the three previews
  python3 _source/build.py --live b     # make style b the live one (saved in site.json)

Three styles share the same data, images, style.css and app.js:
  a  Lookbook   the logo, then every garment as a tile that turns into a group wearing it
  b  Kampanje   a wall of group photos behind the logo with the groups' chest logos running
                underneath, the garments as product cards you swipe or pick by name, the
                custom pieces, then the groups
  c  Indeks     a black index you open garment by garment, the groups as a name list

In a and c a garment opens a lightbox: its model photo(s) first, then the groups wearing it.
In b a garment card opens that garment's own page, <id>.html (frostlinenorge.no/hoodie):
its product photos in each colour, the surname drawn on the back for the garments that
carry one, then the groups wearing it. The product photos and their colours come from
shop.json (make_shop_images.py), the names are drawn in Varsity (varsity.py).
The size guide is storrelser.html (frostlinenorge.no/storrelser), one garment at a time, and
each garment page opens its own table in a sheet; the numbers and where the measuring lines
sit on the photos are sizes.json (its _note says where every number comes from).
index.html is the site. The styles listed in site.json "published" are also written as
<style>.html (frostlinenorge.no/a, /b) so they can be compared on the real domain;
those carry noindex and point canonical at the front page. preview-a/b/c.html are the
same for local use only (gitignored).
"""
import json, os, re, sys, html, hashlib, datetime, math, urllib.parse
from PIL import Image, ImageOps

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
sys.path.insert(0, S)
from varsity import svg as varsity  # noqa: E402
E = html.escape
IG = 'https://www.instagram.com/frostlineno/'
DM = 'https://ig.me/m/frostlineno'
STYLES = ('a', 'b', 'c')

site_path = f'{S}/site.json'
site = json.load(open(site_path)) if os.path.exists(site_path) else {'live': 'a'}
if '--live' in sys.argv:
    site['live'] = sys.argv[sys.argv.index('--live') + 1]
    if site['live'] not in STYLES:
        sys.exit(f'--live takes one of {STYLES}')
    json.dump(site, open(site_path, 'w'), indent=1, ensure_ascii=False)

# the domain this site is served on (also written to CNAME), and the skoleklær store's address;
# with "forward" set, any path this site does not have goes on to that address (404.html),
# so links to the store made while it lived on this domain keep working (see the end)
URL = f"https://{site.get('domain', 'frostlinenorge.no')}/"
SKOLE = site.get('skole', 'https://skole.frostlinenorge.no/')

posts = {p['n']: p for p in json.load(open(f'{S}/posts.json'))}
groups = json.load(open(f'{S}/groups.json'))
PRODUCTS = json.load(open(f'{S}/products.json'))['products']

_dims = {}
def dims(b):
    if b not in _dims:
        _dims[b] = Image.open(f'{SITE}/img/{b}-m.webp').size
    return _dims[b]

group_of = {}
for g in groups:
    for n in [g['n']] + g.get('also', []):
        group_of[n] = g['name']

GROUPS = []
for g in groups:
    files = []
    for n in [g['n']] + g.get('also', []):
        files += [i['file'][:-4] for i in posts[n]['images'] if i['ok']]
    order = [g['cover']] + [f for f in files if f != g['cover']]
    GROUPS.append({'name': g['name'], 'imgs': [{'b': f, 'w': dims(f)[0], 'h': dims(f)[1]} for f in order]})
for p in PRODUCTS:
    p['worn_imgs'] = [{'b': b, 'w': dims(b)[0], 'h': dims(b)[1], 'g': group_of[b.split('-')[0]]} for b in p['worn']]
N_GROUPS = len(GROUPS)

# the product photos per garment: its cuts (bukse and shorts: unisex, dame), per cut its
# colours, per colour a front and maybe a back (make_shop_images.py)
SHOP = json.load(open(f'{S}/shop.json'))
COLOURS = SHOP['colours']
CUT_NAME = {'unisex': 'Unisex', 'dame': 'Dame'}
# Where the surname goes on a back photo, in % of the square frame: left, top, width, height.
# The type is as tall as the box and shrinks only when a long name reaches its width, so the
# box is as wide as the back allows with a hand's width of clear fabric to each side seam
# (the grey backs, the narrowest, have their seams at about 27.5 and 72.7 % of the frame at
# this height, the sleeves hanging right beside them), and its bottom stays above the ribbed
# hem (zip 86 %, hoodie 85 %). Bigger than the skole store's 35 x 7.5 box: BURUM-AUENSEN read
# too small there (Alexander, 2026-09-27). 44 % wide was tried and ran seam to seam.
NAME_BOX = {'zip-hoodie': (30, 72, 40, 10), 'hoodie': (31.3, 72, 38, 10)}
for p in PRODUCTS:
    p['cuts'] = SHOP['garments'][p['id']]
    # a colour once, in the order the cuts show them (the card's swatches)
    p['colours'] = list(dict.fromkeys(c['k'] for cut in p['cuts'] for c in cut['colours']))

# the size guide: per garment its cuts, each a product photo to draw the measuring lines on and
# a table (sizes.json); a garment missing there (the college jacket) has no size guide
SIZES = json.load(open(f'{S}/sizes.json'))
SIZE_OF = SIZES['garments']
SIZED = [p for p in PRODUCTS if p['id'] in SIZE_OF]

# one-off pieces made for a single group (custom.json), photos in img/c/
CUSTOM = json.load(open(f'{S}/custom.json'))['custom']
for c in CUSTOM:
    c['imgs'] = [{'b': 'c/' + f.rsplit('.', 1)[0]} for f in c['photos']]
    for im in c['imgs']:
        im['w'], im['h'] = dims(im['b'])

# each group's own chest logo (make_logos.py), in the order of the group photos;
# a group without one is left out
LOGOS = []
for gi, g in enumerate(groups):
    f = f'img/logo/{g["n"]}.webp'
    if os.path.exists(f'{SITE}/{f}'):
        w, h = Image.open(f'{SITE}/{f}').size
        LOGOS.append({'gi': gi, 'name': g['name'], 'f': f, 'w': w, 'h': h})

# lightbox sets: p<i> is a garment (model photos, then the groups in it), g<i> a group,
# c<i> a custom piece
DATA = {'s': {}}
for i, p in enumerate(PRODUCTS):
    model = [{'s': f'img/p/{pid}-model-1000.webp', 'w': 1000, 'h': 1000, 'c': cut} for pid, cut in p['photos']]  # stamped below
    DATA['s'][f'p{i}'] = {'t': p['name'], 'k': 'p', 'imgs': model + p['worn_imgs']}
for i, g in enumerate(GROUPS):
    DATA['s'][f'g{i}'] = {'t': g['name'], 'k': 'g', 'imgs': g['imgs']}
for i, c in enumerate(CUSTOM):
    DATA['s'][f'c{i}'] = {'t': c['group'], 'k': 'c', 'w': c['what'], 'imgs': c['imgs']}

TITLE = 'Frostline'
DESC = ('Frostline lager russeklær for russegrupper: zip hoodie, hoodie, crewneck, bukse, shorts, '
        't-skjorte, longsleeve, singlet og collegejakke med gruppas eget trykk. Kontakt oss på Instagram @frostlineno.')
# who Frostline is, for search engines only (nothing of this shows on the page): the name
# people search for, what the company makes, the Instagram account and the school store
# that belong to it
LD = {
    '@context': 'https://schema.org',
    '@graph': [
        {'@type': 'Organization', '@id': URL + '#org', 'name': 'Frostline', 'alternateName': 'Frostline Norge',
         'legalName': 'Frostec AS', 'url': URL,
         'logo': {'@type': 'ImageObject', 'url': URL + 'assets/frostline-logo.png', 'width': 992, 'height': 142},
         'image': URL + 'assets/og.jpg',
         'description': 'Frostline lager russeklær og skoleklær med gruppas eget trykk: zip hoodie, hoodie, '
                        'crewneck, bukse, shorts, t-skjorte, longsleeve, singlet og collegejakke.',
         'areaServed': {'@type': 'Country', 'name': 'Norge'},
         'knowsAbout': ['Russeklær', 'Russegrupper', 'Skoleklær', 'Klær med eget trykk'],
         'sameAs': [IG, SKOLE],
         'contactPoint': {'@type': 'ContactPoint', 'contactType': 'customer service', 'url': IG,
                          'availableLanguage': 'Norwegian'}},
        {'@type': 'WebSite', '@id': URL + '#site', 'url': URL, 'name': 'Frostline',
         'alternateName': 'Frostline Norge', 'inLanguage': 'nb-NO', 'publisher': {'@id': URL + '#org'}},
        {'@type': 'WebPage', '@id': URL + '#page', 'url': URL, 'name': 'Frostline', 'inLanguage': 'nb-NO',
         'isPartOf': {'@id': URL + '#site'}, 'about': {'@id': URL + '#org'},
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': URL + 'assets/og.jpg', 'width': 1200, 'height': 630}},
    ],
}

ICON_IG = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/>'
           '<circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>')
ICON_STACK = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="7" width="14" height="14" rx="2"/>'
              '<path d="M3 17V5a2 2 0 0 1 2-2h12"/></svg>')
ICON_RULER = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 16.5 16.5 2.5l5 5-14 14z"/>'
              '<path d="M6 13l1.8 1.8M9.5 9.5l2.6 2.6M13 6l1.8 1.8"/></svg>')
CHEV = {-1: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
        1: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>'}


def version(f):
    return hashlib.md5(open(f'{SITE}/{f}', 'rb').read()).hexdigest()[:8]


def photo(b, alt, sizes, eager=False, large=False, cls=''):
    """An Instagram photo, img/<post>-<slide>-{s,m,l}.webp."""
    w, h = dims(b)
    srcset = f'img/{b}-s.webp 480w, img/{b}-m.webp 900w' + (f', img/{b}-l.webp 1440w' if large else '')
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="img/{b}-m.webp" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{E(alt)}"{load} decoding="async">')


def model_src(pid, w):
    """A model photo's URL, stamped with its content so a new photo is never served from cache."""
    f = f'img/p/{pid}-model-{w}.webp'
    return f'{f}?v={version(f)}'


def model_alt(p, cut):
    return f"{p['name']} fra Frostline på modell" + (f", {cut.lower()}" if cut else '')


def model_img(p, k, sizes, cls=''):
    """The k-th on-model photo of a garment, img/p/<id>-model-{600,1000}.webp."""
    pid, cut = p['photos'][k]
    c = f' class="{cls}"' if cls else ''
    big, small = model_src(pid, 1000), model_src(pid, 600)
    return (f'<img{c} src="{big}" srcset="{small} 600w, {big} 1000w" sizes="{sizes}" width="1000" height="1000" '
            f'alt="{E(model_alt(p, cut))}" loading="lazy" decoding="async">')


def second_look(p, sizes):
    """What a tile turns into on hover: the garment on a group, else its other cut."""
    if p['worn_imgs']:
        im = p['worn_imgs'][0]
        return photo(im['b'], f"Russegruppa {im['g']} i {p['lname']} fra Frostline", sizes, cls='alt')
    if len(p['photos']) > 1:
        return model_img(p, 1, sizes, cls='alt')
    return ''


def count(p):
    n = len(p['photos']) + len(p['worn_imgs'])
    return f'<span class="count" aria-hidden="true">{ICON_STACK}{n}</span>'


def open_label(p):
    return f"{p['name']}: se bilder"


def rail(p, pi):
    offset = len(p['photos'])
    n = offset + len(p['worn_imgs'])
    tiles = ''.join(
        f'<button class="tile" type="button" data-s="p{pi}" data-i="{offset + k}" aria-label="{E(im["g"])}, bilde {offset + k + 1} av {n}">'
        + photo(im['b'], f"Russegruppa {im['g']} i {p['lname']} fra Frostline",
                '(min-width: 960px) 240px, (min-width: 640px) 38vw, 62vw')
        + f'<span class="tile-g">{E(im["g"])}</span></button>'
        for k, im in enumerate(p['worn_imgs']))
    arrows = ''.join(f'<button class="arr" type="button" data-dir="{d}" aria-label="{"Forrige" if d < 0 else "Neste"} bilder">{CHEV[d]}</button>' for d in (-1, 1))
    return (f'<div class="worn"><div class="arrows">{arrows}</div>'
            f'<div class="rail">{tiles}</div></div>')


def marquee():
    items = ''.join(f'<span>{E(g["name"])}</span><i>✦</i>' for g in GROUPS)
    return f'<div class="marquee" aria-hidden="true"><div class="marquee-track">{items}{items}</div></div>'


def logo_h1(extra=''):
    return (f'<h1 class="hero-logo"{extra}><img src="assets/frostline-logo-outline.webp" alt="Frostline" '
            f'width="1800" height="249" fetchpriority="high"></h1>')


def head(style, preview, title=TITLE, desc=DESC, url=URL, og=('assets/og.jpg', 1200, 630), ld=LD,
         css=(), fonts='', body='', home=False, skip='#produkter'):
    """The top of a page up to the bar. The front page takes the defaults; a product page
    passes its own title, description, address, link-preview picture and JSON-LD, shop.css
    and Bebas Neue (the surname), and a bar with the logo going home."""
    robots = '<meta name="robots" content="noindex">\n' if preview else ''
    styles = ''.join(f'<link rel="stylesheet" href="{c}?v={version(c)}">\n' for c in ('style.css', f'v-{style}.css') + tuple(css))
    preload = '' if home else '<link rel="preload" as="image" href="assets/frostline-logo-outline.webp" fetchpriority="high">\n'
    logo = ('<a class="home" href="./" aria-label="Frostline, til forsiden">'
            '<img src="assets/frostline-logo-white.png" alt="Frostline" width="992" height="142"></a>\n') if home else ''
    return f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{robots}<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Frostline">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="{URL}{og[0]}">
<meta property="og:image:width" content="{og[1]}">
<meta property="og:image:height" content="{og[2]}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="nb_NO">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#09090b">
<link rel="icon" href="assets/favicon.png?v={version('assets/favicon.png')}" type="image/png" sizes="96x96">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png?v={version('assets/apple-touch-icon.png')}">
{preload}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,500;9..40,700;9..40,800&family=Graduate{fonts}&display=swap" rel="stylesheet">
{styles}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body class="v-{style}{' ' + body if body else ''}">
<a class="skip" href="{skip}">Hopp til innholdet</a>
<header class="bar"><div class="bar-in">
{logo}<a class="dm" href="{DM}" target="_blank" rel="noopener" aria-label="Send oss en DM på Instagram">{ICON_IG}<span>DM</span></a>
</div></header>
'''


def tail(data=None, scripts=(), here=''):
    """Contact, footer, the lightbox and the scripts. data: the lightbox sets this page opens;
    here: the footer link that is this page."""
    js = ''.join(f'<script src="{s}?v={version(s)}"></script>\n' for s in ('app.js',) + tuple(scripts))
    cur = ' aria-current="page"' if here == 'storrelser' else ''
    return f'''<section class="ig" id="kontakt" aria-labelledby="ig-h">
<h2 class="sr" id="ig-h">Kontakt oss på Instagram</h2>
<a class="handle" href="{IG}" target="_blank" rel="noopener">@frostlineno</a>
<a class="btn" href="{DM}" target="_blank" rel="noopener" aria-label="Send oss en DM på Instagram">{ICON_IG}<span>DM</span></a>
</section>
</main>
<footer class="foot">
<a class="foot-a" href="storrelser"{cur}>Størrelser</a>
<img src="assets/frostline-logo-white.png" alt="" width="992" height="142" loading="lazy">
</footer>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Bildevisning">
<button class="lb-close" type="button" aria-label="Lukk">&times;</button>
<button class="lb-prev" type="button" aria-label="Forrige">&#8249;</button>
<button class="lb-next" type="button" aria-label="Neste">&#8250;</button>
<figure class="lb-fig"><img id="lb-img" alt=""><figcaption id="lb-cap"></figcaption></figure>
</div>
<script id="data" type="application/json">{json.dumps(DATA if data is None else data, ensure_ascii=False, separators=(',', ':'))}</script>
{js}</body>
</html>
'''


def group_cards(sizes, cls='gcard'):
    out = []
    for gi, g in enumerate(GROUPS):
        n = len(g['imgs'])
        out.append(
            f'<li><button class="{cls} reveal" type="button" data-s="g{gi}" data-i="0" aria-label="{E(g["name"])}: se {n} bilder">'
            + photo(g['imgs'][0]['b'], f"Russegruppa {g['name']} i klær fra Frostline", sizes)
            + f'<span class="glabel"><span class="gname">{E(g["name"])}</span></span></button></li>')
    return ''.join(out)


# ---------------------------------------------------------------- a: Lookbook
def body_a():
    n = len(PRODUCTS)
    def sizes(pi):
        # a phone shows two across, except an odd last tile, which runs full width
        phone = '92vw' if pi == n - 1 and n % 2 else '46vw'
        return f'(min-width: 1240px) 390px, (min-width: 600px) 31vw, {phone}'
    tiles = ''.join(
        f'<li id="{p["id"]}"><button class="ptile" type="button" data-s="p{pi}" data-i="0" aria-label="{E(open_label(p))}">'
        f'<span class="ptile-img shot">{model_img(p, 0, sizes(pi))}{second_look(p, sizes(pi))}{count(p)}</span>'
        f'<span class="ptile-name">{E(p["name"])}</span></button></li>'
        for pi, p in enumerate(PRODUCTS))
    return f'''<main>
<section class="hero" id="top">
{logo_h1()}
</section>
<section class="catalog" id="produkter" aria-labelledby="p-h">
<div class="wrap">
<h2 class="sr" id="p-h">Russeklær</h2>
<ul class="pgrid">{tiles}</ul>
</div>
</section>
{marquee()}
<section class="groups" id="grupper" aria-labelledby="g-h">
<div class="wrap">
<h2 class="sr" id="g-h">Russegruppene</h2>
<ul class="ggrid">{group_cards('(min-width: 1080px) 290px, (min-width: 720px) 31vw, 48vw')}</ul>
</div>
</section>
'''


# ---------------------------------------------------------------- b: Kampanje
def mosaic():
    """A grey wall of group covers for the style-b hero, 8 x 3 tiles."""
    cols, rows, tw, th = 8, 3, 200, 250
    wall = Image.new('RGB', (cols * tw, rows * th), (9, 9, 11))
    covers = [g['imgs'][0]['b'] for g in GROUPS][:cols * rows]
    for k, b in enumerate(covers):
        im = ImageOps.fit(Image.open(f'{SITE}/img/{b}-s.webp').convert('L'), (tw, th), Image.LANCZOS)
        wall.paste(im.convert('RGB'), ((k % cols) * tw, (k // cols) * th))
    wall.save(f'{SITE}/assets/mosaic.jpg', quality=60, optimize=True, progressive=True)
    return wall.size


def logo_ticker():
    """The groups' chest logos running under the hero, twice over so the loop has no seam.
    Each opens that group's photos. Like the photo wall behind the logo they carry data-src,
    not src: app.js starts them once the Frostline logo is in, so a slow phone gets the logo
    first instead of sharing the line with 27 other pictures."""
    def items(copy):
        extra = ' tabindex="-1"' if copy else ''
        return ''.join(
            f'<li><button class="lg" type="button" data-s="g{l["gi"]}" data-i="0" aria-label="{E(l["name"])}"{extra}>'
            f'<img data-src="{l["f"]}?v={version(l["f"])}" alt="" width="{l["w"]}" height="{l["h"]}" '
            f'style="--f:{l["h"] / 128:.3f}" decoding="async"></button></li>'
            for l in LOGOS)
    return (f'<div class="logos" role="region" aria-label="Russegrupper i Frostline">'
            f'<div class="logos-track"><ul>{items(False)}</ul><ul aria-hidden="true">{items(True)}</ul></div></div>')


def credit(name):
    return f'<span class="credit">{E(name)}</span>'


def shop_src(name, w):
    """A product photo's URL, stamped with its content like the model photos."""
    f = f'img/shop/{name}-{w}.webp'
    return f'{f}?v={version(f)}'


def shop_srcset(name):
    return f'{shop_src(name, 600)} 600w, {shop_src(name, 1200)} 1200w'


def shop_img(name, sizes, alt, cls='', eager=False):
    """A garment on white, img/shop/<name>-{600,1200}.webp (make_shop_images.py)."""
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="{shop_src(name, 600)}" srcset="{shop_srcset(name)}" sizes="{sizes}" width="1200" '
            f'height="1200" alt="{E(alt)}"{load} decoding="async">')


def cname(k):
    return COLOURS[k]['name']


def shop_alt(p, k, view='front', cut=''):
    side = {'front': 'forfra', 'back': 'bakfra'}[view]
    return f"{p['name']}{' ' + cut if cut else ''} fra Frostline i {cname(k).lower()}, {side}"


CARD_SIZES = '(min-width: 1300px) 360px, (min-width: 900px) 30vw, (min-width: 600px) 44vw, 72vw'


def card(p):
    """A garment as a product card: its photo on white, the name in Varsity, a dot per colour.
    The card opens the garment's page. Pointing at a dot shows that colour on the card, and
    the dot itself opens the page in that colour (<id>#navy)."""
    front = {}
    for cut in p['cuts']:  # a colour the first cut lacks comes from the next cut that has it
        for c in cut['colours']:
            front.setdefault(c['k'], c['front'])
    k0 = p['colours'][0]
    dots = ''.join(
        f'<a class="sw{" on" if k == k0 else ""}" href="{p["id"]}#{k}" style="--c:{COLOURS[k]["hex"]}" '
        f'data-src="{shop_src(front[k], 600)}" data-srcset="{shop_srcset(front[k])}" '
        f'aria-label="{E(p["name"])} i {cname(k).lower()}"></a>'
        for k in p['colours'])
    img = shop_img(front[k0], CARD_SIZES, shop_alt(p, k0), cls='pc-im')
    num = PRODUCTS.index(p) + 1
    return (f'<article class="pc" id="{p["id"]}"><a class="pc-link" href="{p["id"]}">'
            f'<span class="pc-num" aria-hidden="true">{num:02d}</span><span class="pc-img">{img}</span>'
            f'<h3 class="pc-name">{varsity(p["name"])}<span class="sr">{E(p["name"])}</span></h3></a>'
            f'<div class="pc-sw">{dots}</div></article>')


def cards_row(items, tabs=True):
    """Garment cards in a row you swipe or step through with the arrows; on the front page
    the names run above it and take you to a card."""
    head = ''
    if tabs:
        head = ('<nav class="car-tabs" aria-label="Plaggene">'
                + ''.join(f'<a class="car-tab" href="#{p["id"]}" aria-current="{"true" if k == 0 else "false"}">{E(p["name"])}</a>'
                          for k, p in enumerate(items)) + '</nav>')
    arrows = ''.join(f'<button class="car-arr" type="button" data-dir="{d}" aria-label="{"Forrige" if d < 0 else "Neste"} plagg">{CHEV[d]}</button>'
                     for d in (-1, 1))
    return (f'<div class="car{"" if tabs else " car-bare"}" data-car>\n'
            f'<div class="car-head">{head}<div class="car-arrows">{arrows}</div></div>\n'
            f'<div class="car-track" tabindex="0" aria-label="Plaggene, sveip for flere">\n'
            + '\n'.join(card(p) for p in items) + '\n</div>\n</div>')


def custom_b():
    """The one-off pieces, big, at the bottom."""
    if not CUSTOM:
        return ''
    items = ''.join(
        f'<li><button class="cust" type="button" data-s="c{ci}" data-i="0" aria-label="{E(c["group"])}: {E(c["what"])}">'
        + photo(c['imgs'][0]['b'], f"Russegruppa {c['group']} i {c['what'].lower()} fra Frostline",
                '(min-width: 1240px) 1180px, 94vw' if len(CUSTOM) == 1 else '(min-width: 720px) 48vw, 94vw', large=True)
        + credit(c['group']) + '</button></li>'
        for ci, c in enumerate(CUSTOM))
    return f'''<section class="custom" id="custom" aria-labelledby="c-h">
<h2 class="custom-h" id="c-h">{varsity('Custom')}<span class="sr">Custom</span></h2>
<ul class="cust-grid{' one' if len(CUSTOM) == 1 else ''}">{items}</ul>
</section>
'''


def body_b():
    """The logo over a wall of the groups, their chest logos running underneath; the
    garments as product cards you swipe or pick by name, each opening its own page; the
    custom pieces; the groups edge to edge."""
    mw, mh = mosaic()
    return f'''<main>
<section class="hero hero-b" id="top">
<img class="hero-bg" data-src="assets/mosaic.jpg?v={version('assets/mosaic.jpg')}" alt="" width="{mw}" height="{mh}" decoding="async">
<div class="hero-in">
{logo_h1()}
</div>
{logo_ticker()}
</section>
<section class="shop" id="produkter" aria-labelledby="p-h">
<h2 class="sr" id="p-h">Russeklær</h2>
{cards_row(PRODUCTS)}
</section>
{custom_b()}<section class="groups-b" id="grupper" aria-labelledby="g-h">
<h2 class="sr" id="g-h">Russegruppene</h2>
<ul class="wall">{group_cards('(min-width: 1280px) 15vw, (min-width: 720px) 25vw, 50vw', 'wcard')}</ul>
</section>
'''


# ---------------------------------------------------------------- the size guide
def cm(v):
    """A measurement the way it is written in Norwegian: 40,5, and 43 without a decimal."""
    return f'{v:g}'.replace('.', ',')


def toward(p, q, d):
    """The point d along the way from p to q."""
    n = math.hypot(q[0] - p[0], q[1] - p[1])
    return p[0] + (q[0] - p[0]) * d / n, p[1] + (q[1] - p[1]) * d / n


def tip(at, frm, length=30, half=12):
    """An arrowhead with its point at `at`, coming from `frm`."""
    (x, y), (fx, fy) = at, frm
    n = math.hypot(x - fx, y - fy)
    ux, uy = (x - fx) / n, (y - fy) / n
    bx, by = x - ux * length, y - uy * length
    return f'M{x:.0f} {y:.0f}L{bx - uy * half:.0f} {by + ux * half:.0f}L{bx + uy * half:.0f} {by - ux * half:.0f}Z'


def along(pts, t):
    """The point a share t of the way along a line through pts."""
    segs = [(a, b, math.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(pts, pts[1:])]
    d = t * sum(s[2] for s in segs)
    for a, b, n in segs:
        if d <= n:
            return toward(a, b, d)
        d -= n
    return pts[-1]


def measure_mark(r):
    """One measurement drawn on the product photo: the line with an arrowhead at each end (the
    line stops under them, so the points are the arrowheads' own) and its letter in a dot, a
    share `at` along it or else in the middle of its longest stretch. All in the photo's
    1200 x 1200 pixels; sizes.css draws it."""
    pts, k = r['mark'], r['k']
    if 'at' in r:
        cx, cy = along(pts, r['at'])
    else:
        a, b = max(zip(pts, pts[1:]), key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    line = [toward(pts[0], pts[1], 22)] + pts[1:-1] + [toward(pts[-1], pts[-2], 22)]
    d = 'M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in line)
    heads = tip(pts[0], pts[1]) + tip(pts[-1], pts[-2])
    return (f'<g class="sg-m" data-k="{k}"><path class="sg-edge" d="{d}"/><path class="sg-ln" d="{d}"/>'
            f'<path class="sg-hd" d="{heads}"/><circle class="sg-dot" cx="{cx:.0f}" cy="{cy:.0f}" r="40"/>'
            f'<text class="sg-tx" x="{cx:.0f}" y="{cy:.0f}" dy=".36em">{k}</text></g>')


SG_PIC = '(min-width: 1240px) 600px, (min-width: 900px) 48vw, 92vw'
SG_PIC_SHEET = '(min-width: 1100px) 480px, (min-width: 700px) 44vw, 56vw'


def shop_thumb(name, w=200):
    """A small copy of a product photo for the size guide's row of garments, made here from
    the 1200 one when it is missing or older than that."""
    src, f = f'{SITE}/img/shop/{name}-1200.webp', f'img/shop/{name}-{w}.webp'
    if not os.path.exists(f'{SITE}/{f}') or os.path.getmtime(f'{SITE}/{f}') < os.path.getmtime(src):
        Image.open(src).resize((w, w), Image.LANCZOS).save(f'{SITE}/{f}', quality=88, method=6)
    return f'{f}?v={version(f)}'


def size_guide(p, level=2, go=False, pic=SG_PIC):
    """A garment's size guide: per cut its product photo with the measuring lines on it and a
    table with the sizes down the side and the measurements across; Unisex / Dame switch
    between the cuts (sizes.js). go: a link on to the garment's own page (on /storrelser);
    pic: the photo's sizes attribute."""
    pid, name, cuts = p['id'], p['name'], SIZE_OF[p['id']]
    labels = SIZES['labels']
    figs, tables = [], []
    for i, c in enumerate(cuts):
        hide = ' hidden' if i else ''
        cut = CUT_NAME.get(c['cut'], '')
        which = f"{name}{' ' + cut.lower() if cut else ''}"
        alt = f"{which} med målene {and_list([r['k'] + ' ' + labels[r['m']].lower() for r in c['rows']])}"
        marks = ''.join(measure_mark(r) for r in c['rows'])
        figs.append(f'<figure class="sg-fig" data-sg-cut="{c["cut"]}"{hide}><div class="sg-pic">'
                    + shop_img(c['img'], pic, alt)
                    + f'<svg class="sg-svg" viewBox="0 0 1200 1200" aria-hidden="true" focusable="false">{marks}</svg>'
                    '</div></figure>')
        cols = ''.join(f'<th scope="col" data-k="{r["k"]}"><span class="sg-key" aria-hidden="true">{r["k"]}</span>'
                       f'{E(labels[r["m"]])}</th>' for r in c['rows'])
        rows = ''.join(f'<tr><th scope="row">{s}</th>'
                       + ''.join(f'<td data-k="{r["k"]}">{cm(r["values"][j])}</td>' for r in c['rows']) + '</tr>'
                       for j, s in enumerate(c['sizes']))
        tables.append(f'<table class="sg-t" data-sg-cut="{c["cut"]}"{hide}><caption class="sr">{E(which)}, mål i cm</caption>'
                      f'<thead><tr><th scope="col"><span class="sr">Størrelse</span></th>{cols}</tr></thead>'
                      f'<tbody>{rows}</tbody></table>')
    pills = ''
    if len(cuts) > 1:
        pills = ('<div class="sg-cuts" role="radiogroup" aria-label="Snitt">'
                 + ''.join(f'<button class="sg-pill" type="button" role="radio" data-cut="{c["cut"]}" '
                           f'aria-checked="{"true" if i == 0 else "false"}">{E(CUT_NAME[c["cut"]])}</button>'
                           for i, c in enumerate(cuts)) + '</div>')
    more = f'<a class="sg-go" href="{pid}">Se plagget{CHEV[1]}</a>' if go else ''
    return (f'<div class="sg" data-g="{pid}"><div class="sg-grid">\n'
            f'<div class="sg-figs">{"".join(figs)}</div>\n'
            f'<div class="sg-side"><h{level} class="sg-name">{varsity(name)}<span class="sr">{E(name)}</span></h{level}>\n'
            f'{pills}{"".join(tables)}\n<p class="sg-note">Mål i cm, plagget liggende flatt.</p>{more}</div>\n'
            f'</div></div>')


def sizes_page():
    """storrelser.html: the size guide, one garment at a time, picked from a row of them;
    storrelser#bukse opens the trousers and #bukse-dame their women's cut (sizes.js). Without
    JavaScript the first garment shows."""
    url = URL + 'storrelser'
    title = 'Størrelser | Frostline'
    desc = (f"Størrelsesguide for russeklær fra Frostline: mål i cm for {and_list([p['lname'] for p in SIZED])}. "
            'Send oss en DM på Instagram @frostlineno.')
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'inLanguage': 'nb-NO',
         'description': desc, 'isPartOf': {'@id': URL + '#site'}, 'about': {'@id': URL + '#org'},
         'breadcrumb': {'@id': url + '#crumbs'}},
        {'@type': 'BreadcrumbList', '@id': url + '#crumbs', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Frostline', 'item': URL},
            {'@type': 'ListItem', 'position': 2, 'name': 'Størrelser', 'item': url}]},
    ]}
    top = head('b', False, title=title, desc=desc, url=url, ld=ld, css=('shop.css', 'sizes.css'),
               body='pp-page sg-page', home=True, skip='#storrelser')
    pick = ''.join(
        f'<a class="sg-pk" href="#{p["id"]}" data-g="{p["id"]}" aria-current="{"true" if i == 0 else "false"}">'
        f'<span class="sg-pk-im"><img src="{shop_thumb(SIZE_OF[p["id"]][0]["img"])}" alt="" width="200" height="200" '
        f'decoding="async"></span><span class="sg-pk-n">{E(p["name"])}</span></a>'
        for i, p in enumerate(SIZED))
    secs = ''.join(
        f'<section class="sg-g" id="sg-{p["id"]}" data-g="{p["id"]}" aria-label="{E(p["name"])}"{" hidden" if i else ""}>\n'
        f'<div class="wrap">{size_guide(p, 2, go=True)}</div>\n</section>\n'
        for i, p in enumerate(SIZED))
    body = f'''<main>
<section class="sg-top" id="storrelser" aria-labelledby="sg-h">
<h1 class="sg-title" id="sg-h">{varsity('Størrelser')}<span class="sr">Størrelser</span></h1>
<nav class="sg-pick" aria-label="Plaggene">{pick}</nav>
</section>
{secs}'''
    return top + body + tail({'s': {}}, ('sizes.js',), here='storrelser')


# ---------------------------------------------------------------- a garment's own page
def and_list(words):
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' og ' + words[-1]


def product_page(p):
    """<id>.html: the garment's photos on white (front, back, on a model) in the colour and
    cut picked beside them, the name in Varsity, for a hoodie or zip hoodie a surname field
    drawn live on the back (pp.js), the DM; then the groups wearing it, then the other
    garments."""
    pid, name = p['id'], p['name']
    url = f'{URL}{pid}'
    navn = bool(p.get('navn'))
    model_k = {cut.lower(): k for k, (_, cut) in enumerate(p['photos'])}

    def pic(n, w_alt):
        return {'s': shop_src(n, 1200), 'ss': shop_srcset(n), 'alt': w_alt}

    cuts = []
    for cut in p['cuts']:
        k = model_k.get(cut['cut'], 0)
        mid, mcut = p['photos'][k]
        cuts.append({
            'k': cut['cut'], 'label': CUT_NAME.get(cut['cut'], ''),
            'model': {'s': model_src(mid, 1000), 'ss': f'{model_src(mid, 600)} 600w, {model_src(mid, 1000)} 1000w',
                      'alt': model_alt(p, mcut)},
            'colours': [{'k': c['k'], 'name': cname(c['k']), 'dark': COLOURS[c['k']]['dark'], 'hex': COLOURS[c['k']]['hex'],
                         'front': pic(c['front'], shop_alt(p, c['k'], 'front', CUT_NAME.get(cut['cut'], '').lower())),
                         'back': pic(c['back'], shop_alt(p, c['k'], 'back', CUT_NAME.get(cut['cut'], '').lower())) if 'back' in c else None}
                        for c in cut['colours']]})
    c0 = cuts[0]['colours'][0]
    views = [('front', c0['front'])] + ([('back', c0['back'])] if c0['back'] else []) + [('model', cuts[0]['model'])]
    sizes_main = '(min-width: 1240px) 640px, (min-width: 900px) 52vw, 100vw'
    stage = (f'<img class="pp-img" id="pp-img" src="{c0["front"]["s"]}" srcset="{c0["front"]["ss"]}" sizes="{sizes_main}" '
             f'width="1200" height="1200" alt="{E(c0["front"]["alt"])}" fetchpriority="high">')
    thumbs = ''.join(
        f'<button class="pp-th" type="button" data-v="{k}" aria-label="{E(v["alt"])}" aria-current="{"true" if k == 0 else "false"}">'
        f'<img src="{v["ss"].split(" ")[0]}" alt="" width="120" height="120" loading="lazy" decoding="async"></button>'
        for k, (_, v) in enumerate(views))
    cut_pills = ''
    if len(cuts) > 1:
        cut_pills = ('<div class="pp-cuts" role="radiogroup" aria-label="Snitt">'
                     + ''.join(f'<button class="pp-pill" type="button" role="radio" data-cut="{k}" data-k="{c["k"]}" '
                               f'aria-checked="{"true" if k == 0 else "false"}">{E(c["label"])}</button>'
                               for k, c in enumerate(cuts)) + '</div>')
    # the size guide opens in a sheet over the page, in the cut the page shows (sizes.js); the
    # link goes to /storrelser where a browser cannot open the sheet
    sized = pid in SIZE_OF
    size_link = size_sheet = ''
    if sized:
        size_link = (f'<a class="pp-size" href="storrelser#{pid}" data-sg-open aria-haspopup="dialog">'
                     f'{ICON_RULER}<span>Størrelser</span></a>\n')
        size_sheet = (f'<dialog class="sg-dlg" id="sg-dlg" aria-labelledby="sg-dlg-h">\n'
                      f'<div class="sg-dlg-bar"><h2 class="sg-dlg-h" id="sg-dlg-h">Størrelser</h2>'
                      f'<button class="sg-x" type="button" aria-label="Lukk">&times;</button></div>\n'
                      f'<div class="sg-dlg-body">{size_guide(p, 3, pic=SG_PIC_SHEET)}</div>\n</dialog>\n')
    swatches = ''.join(
        f'<button class="pp-sw" type="button" role="radio" data-col="{k}" style="--c:{c["hex"]}" '
        f'aria-checked="{"true" if k == 0 else "false"}" aria-label="{E(c["name"])}"></button>'
        for k, c in enumerate(cuts[0]['colours']))
    field = ''
    if navn:
        field = ('<label class="pp-field"><span class="sr">Etternavn på ryggen</span>'
                 '<input class="pp-in" id="pp-in" type="text" maxlength="18" placeholder="Etternavn" autocomplete="off" '
                 'autocapitalize="characters" spellcheck="false" enterkeyhint="done">'
                 '<span class="pp-count" id="pp-count" aria-hidden="true">0/18</span></label>')
    worn = p['worn_imgs']
    worn_html = ''
    if worn:
        tiles = ''.join(
            f'<li><button class="pp-wt" type="button" data-s="w" data-i="{k}" aria-label="{E(im["g"])}, bilde {k + 1} av {len(worn)}">'
            + photo(im['b'], f"Russegruppa {im['g']} i {p['lname']} fra Frostline", '(min-width: 1100px) 290px, (min-width: 720px) 31vw, 48vw')
            + credit(im['g']) + '</button></li>'
            for k, im in enumerate(worn))
        worn_html = (f'<section class="pp-worn" aria-labelledby="w-h">\n<div class="wrap">\n'
                     f'<h2 class="sr" id="w-h">Russegrupper i {E(p["lname"])} fra Frostline</h2>\n'
                     f'<ul class="pp-wgrid">{tiles}</ul>\n</div>\n</section>\n')
    others = [q for q in PRODUCTS if q['id'] != pid]
    data = {'n': name, 'navn': navn, 'box': NAME_BOX.get(pid), 'cuts': cuts}

    colours = and_list([cname(k).lower() for k in p['colours']])
    cut_names = [CUT_NAME.get(c['cut'], '') for c in p['cuts']]
    lead = (and_list([cut_names[0] + '-'] + [c.lower() + '-' for c in cut_names[1:]])[:-1] + 'modell i'
            if len(cut_names) > 1 else 'Finnes i')
    desc = (f"{name} fra Frostline med russegruppas eget trykk" + (' og etternavnet ditt på ryggen' if navn else '')
            + f". {lead} {colours}. Send oss en DM på Instagram @frostlineno.")
    img0 = p['cuts'][0]['colours'][0]['front']
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': f'{name} | Frostline', 'inLanguage': 'nb-NO',
         'description': desc, 'isPartOf': {'@id': URL + '#site'}, 'about': {'@id': URL + '#org'},
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': f'{URL}img/shop/{img0}-og.jpg', 'width': 1200, 'height': 1200},
         'breadcrumb': {'@id': url + '#crumbs'}},
        {'@type': 'BreadcrumbList', '@id': url + '#crumbs', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Frostline', 'item': URL},
            {'@type': 'ListItem', 'position': 2, 'name': name, 'item': url}]},
    ]}
    top = head('b', False, title=f'{name} | Frostline', desc=desc, url=url, og=(f'img/shop/{img0}-og.jpg', 1200, 1200),
               ld=ld, css=('shop.css',) + (('sizes.css',) if sized else ()), fonts='&family=Bebas+Neue' if navn else '',
               body='pp-page', home=True, skip='#produkt')
    body = f'''<main>
<section class="pp" id="produkt" aria-labelledby="pp-h">
<div class="wrap pp-top">
<div class="pp-gal">
<div class="pp-stage" id="pp-stage">{stage}<span class="pp-name" id="pp-name" hidden></span>
<button class="pp-arr" type="button" data-dir="-1" aria-label="Forrige bilde">{CHEV[-1]}</button>
<button class="pp-arr" type="button" data-dir="1" aria-label="Neste bilde">{CHEV[1]}</button></div>
<div class="pp-thumbs" id="pp-thumbs">{thumbs}</div>
</div>
<div class="pp-info">
<h1 class="pp-h" id="pp-h">{varsity(name)}<span class="sr">{E(name)}</span></h1>
{cut_pills}<div class="pp-opt"><p class="pp-lab" id="pp-lab">Farge: <b id="pp-cn">{E(c0['name'])}</b></p>
<div class="pp-sws" id="pp-sws" role="radiogroup" aria-labelledby="pp-lab">{swatches}</div></div>
{size_link}{field}<a class="btn pp-dm" href="{DM}" target="_blank" rel="noopener">{ICON_IG}<span>Send DM</span></a>
</div>
</div>
<script id="pp-data" type="application/json">{json.dumps(data, ensure_ascii=False, separators=(',', ':'))}</script>
</section>
{size_sheet}{worn_html}<section class="pp-more" aria-labelledby="m-h">
<h2 class="sr" id="m-h">Flere plagg fra Frostline</h2>
{cards_row(others, tabs=False)}
</section>
'''
    lb = {'s': {'w': {'t': name, 'k': 'p', 'imgs': worn}}}
    return top + body + tail(lb, ('pp.js',) + (('sizes.js',) if sized else ()))


# ---------------------------------------------------------------- c: Indeks
def body_c():
    rows = []
    for pi, p in enumerate(PRODUCTS):
        pid = p['photos'][0][0]
        models = ''.join(
            f'<button class="model shot" type="button" data-s="p{pi}" data-i="{k}" aria-label="{E(model_alt(p, cut))}">'
            f'{model_img(p, k, "(min-width: 900px) 420px, 50vw")}</button>'
            for k, (_, cut) in enumerate(p['photos']))
        rows.append(f'''<details class="row" id="{p['id']}">
<summary><span class="row-num">{pi + 1:02d}</span><span class="row-name">{E(p['name'])}</span><span class="row-plus" aria-hidden="true"></span>
<img class="row-peek" src="{model_src(pid, 600)}" alt="" width="600" height="600" loading="lazy"></summary>
<div class="row-body">
<div class="models">{models}</div>
{rail(p, pi) if p['worn_imgs'] else ''}
</div>
</details>''')
    names = []
    for gi, g in enumerate(GROUPS):
        cov = g['imgs'][0]['b']
        names.append(f'<li><button class="name" type="button" data-s="g{gi}" data-i="0" data-cover="{cov}">'
                     + photo(cov, '', '64px', cls='name-thumb')
                     + f'<span class="nm">{E(g["name"])}</span></button></li>')
    first = GROUPS[0]['imgs'][0]['b']
    fw, fh = dims(first)
    return f'''<main>
<section class="hero hero-c" id="top">
{logo_h1()}
<a class="scroll-cue" href="#produkter" aria-label="Til plaggene"><span></span></a>
</section>
<section class="index" id="produkter" aria-labelledby="i-h">
<div class="wrap">
<h2 class="sr" id="i-h">Russeklær</h2>
<div class="rows">{''.join(rows)}</div>
</div>
</section>
<section class="roster" id="grupper" aria-labelledby="r-h">
<div class="wrap">
<h2 class="sr" id="r-h">Russegruppene</h2>
<div class="roster-grid">
<ol class="names">{''.join(names)}</ol>
<figure class="peek" aria-hidden="true"><img id="peek-img" src="img/{first}-m.webp" width="{fw}" height="{fh}" alt="" loading="lazy"></figure>
</div>
</div>
</section>
'''


for st in DATA['s'].values():
    for im in st['imgs']:
        if 's' in im and '?v=' not in im['s']:
            im['s'] += f"?v={version(im['s'])}"

BODIES = {'a': body_a, 'b': body_b, 'c': body_c}


def page(style, preview=False):
    return head(style, preview, css=('shop.css',) if style == 'b' else ()) + BODIES[style]() + tail()


for s in STYLES:
    open(f'{SITE}/preview-{s}.html', 'w').write(page(s, preview=True))
published = site.get('published', [])
for s in STYLES:
    if s in published:
        open(f'{SITE}/{s}.html', 'w').write(page(s, preview=True))
    elif os.path.exists(f'{SITE}/{s}.html'):
        os.remove(f'{SITE}/{s}.html')
live = page(site['live'])
open(f'{SITE}/index.html', 'w').write(live)
# every garment's own page (the cards of style b open them), and the size guide
pages = {p['id']: product_page(p) for p in PRODUCTS}
pages['storrelser'] = sizes_page()
for pid, h in pages.items():
    open(f'{SITE}/{pid}.html', 'w').write(h)

today = datetime.date.today().isoformat()


def pictures(h):
    """Every picture on a page that says what it shows (the groups in their garments, the
    garments on white and on a model), so image search can find them too."""
    pics = []
    for src in re.findall(r'<img[^>]*?\ssrc="([^"]+)"[^>]*?\salt="([^"]+)"', h):
        if not src[0].startswith('assets/') and src[0] not in pics:
            pics.append(src[0])
    return ''.join(f'<image:image><image:loc>{E(URL + s)}</image:loc></image:image>' for s in pics)


urls = [(URL, live)] + [(URL + pid, h) for pid, h in pages.items()]
open(f'{SITE}/sitemap.xml', 'w').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
    + ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod>{pictures(h)}</url>\n' for u, h in urls)
    + '</urlset>\n')
open(f'{SITE}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /_source/\nDisallow: /preview-\nSitemap: {URL}sitemap.xml\n')
# GitHub rewrites CNAME without a newline when the domain is set in its settings; leave the file
# alone while it names the same host, so a build does not touch it for nothing
host = URL.split('/')[2]
if not os.path.exists(f'{SITE}/CNAME') or open(f'{SITE}/CNAME').read().strip() != host:
    open(f'{SITE}/CNAME', 'w').write(host + '\n')

# The school store lived on this domain until 2026-09-28, so links to it are out there: the
# /<school> short links handed to the schools, product and cart links, the order-status links in
# its e-mails. With "forward" set they keep working:
#  - 404.html, for a path this site does not have: one of its own pages written differently
#    (/Hoodie, /hoodie/, /hoodie.html) goes to that page; anything else goes on to the store at
#    the same path, query and #fragment. Without JavaScript it sends you to the store's front.
#  - the short links in "store_links" also get a page of their own that forwards with a
#    0-second refresh, so they answer 200 and work without JavaScript and in link previews.
# (Pictures cannot be forwarded like that: the e-mail signature logos the store served are kept
# as copies at the same paths, cdn/shop/t/2/assets/.)
OWN = [''] + list(pages) + [s for s in STYLES if s in published]
LINKS = site.get('store_links', []) if site.get('forward') else []
FORWARD_MARK = '<!-- forwards to the school store (build.py store_links) -->'
for f in os.listdir(SITE):
    if f.endswith('.html') and f[:-5] not in LINKS and FORWARD_MARK in open(f'{SITE}/{f}').read():
        os.remove(f'{SITE}/{f}')
for slug in LINKS:
    if slug in OWN:
        sys.exit(f'store_links: /{slug} is a page of this site')
    to = SKOLE + urllib.parse.quote(slug)
    open(f'{SITE}/{slug}.html', 'w').write(f'''<!DOCTYPE html>
{FORWARD_MARK}
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frostline</title>
<link rel="canonical" href="{E(to)}">
<meta http-equiv="refresh" content="0; url={E(to)}">
</head>
<body style="margin:0;padding:32px 16px;background:#09090b;font:600 16px/1.5 system-ui,sans-serif">
<a href="{E(to)}" style="color:#fff">{E(to.split('//')[1])}</a>
</body>
</html>
''')
if site.get('forward'):
    to = SKOLE.rstrip('/')
    open(f'{SITE}/404.html', 'w').write(f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Frostline</title>
<script>(function(){{
  var l=location,own={json.dumps(OWN)},p=l.pathname.replace(/\\.html$/i,'').replace(/\\/+$/,'').slice(1).toLowerCase();
  if(own.indexOf(p)>=0&&l.pathname!=='/'+p)l.replace('/'+p+l.search+l.hash);
  else l.replace({json.dumps(to)}+l.pathname+l.search+l.hash);
}})()</script>
<noscript><meta http-equiv="refresh" content="0; url={E(SKOLE)}"></noscript>
</head>
<body style="margin:0;padding:32px 16px;background:#09090b;font:600 16px/1.5 system-ui,sans-serif">
<a href="{E(SKOLE)}" style="color:#fff">{E(SKOLE.split('/')[2])}</a>
</body>
</html>
''')
elif os.path.exists(f'{SITE}/404.html'):
    os.remove(f'{SITE}/404.html')

n_imgs = sum(len(g['imgs']) for g in GROUPS)
print(f"live style {site['live']}, garments {len(PRODUCTS)} (a page each), groups {N_GROUPS}, group photos {n_imgs}, "
      f"garment photos {sum(len(p['worn']) for p in PRODUCTS)}, index.html {len(live)} bytes")
