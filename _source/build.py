"""Build the site from the JSON files in _source/.

  python3 _source/build.py              # index.html in the live style, plus the three previews
  python3 _source/build.py --live b     # make style b the live one (saved in site.json)

Three styles share the same data, images, style.css and app.js:
  a  Lookbook   the logo over the four garments, a studio for each, the groups as a grid
  b  Kampanje   a wall of group photos behind the logo, one big photo panel per garment
  c  Indeks     a black index you open garment by garment, the groups as a name list

preview-a.html, preview-b.html and preview-c.html are for choosing locally; they are
gitignored and carry noindex. Only index.html is the site.
"""
import json, os, sys, html, hashlib, datetime
from PIL import Image, ImageOps

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
E = html.escape
URL = 'https://russ.frostlinenorge.no/'
IG = 'https://www.instagram.com/frostlineno/'
DM = 'https://ig.me/m/frostlineno'
STYLES = ('a', 'b', 'c')

site_path = f'{S}/site.json'
site = json.load(open(site_path)) if os.path.exists(site_path) else {'live': 'a'}
if '--live' in sys.argv:
    site['live'] = sys.argv[sys.argv.index('--live') + 1]
    if site['live'] not in STYLES:
        sys.exit(f'--live takes one of {STYLES}')
    json.dump(site, open(site_path, 'w'), indent=1)

posts = {p['n']: p for p in json.load(open(f'{S}/posts.json'))}
groups = json.load(open(f'{S}/groups.json'))
cat = json.load(open(f'{S}/products.json'))
COLORS, PRODUCTS = cat['colors'], cat['products']

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

DATA = {'s': {}, 'p': [], 'c': COLORS}
for i, p in enumerate(PRODUCTS):
    DATA['s'][f'p{i}'] = {'t': p['name'], 'k': 'p', 'imgs': p['worn_imgs']}
    DATA['p'].append({'name': p['name'], 'lname': p['lname'], 'cuts': p['img']})
for i, g in enumerate(GROUPS):
    DATA['s'][f'g{i}'] = {'t': g['name'], 'k': 'g', 'imgs': g['imgs']}

TITLE = 'Frostline | Russeklær for russegrupper'
DESC = ('Frostline lager russeklær for russegrupper: zip hoodie, hoodie, crewneck og bukse '
        'med gruppas eget trykk. Se plaggene og gruppene som går i dem. Kontakt oss på Instagram.')
LD = {
    '@context': 'https://schema.org',
    '@graph': [
        {'@type': 'Organization', '@id': URL + '#org', 'name': 'Frostline', 'legalName': 'Frostec AS',
         'url': URL, 'logo': URL + 'assets/frostline-logo.png',
         'sameAs': [IG, 'https://frostlinenorge.no/'],
         'contactPoint': {'@type': 'ContactPoint', 'contactType': 'customer service', 'url': IG,
                          'availableLanguage': 'Norwegian'}},
        {'@type': 'WebSite', '@id': URL + '#site', 'url': URL, 'name': 'Frostline', 'inLanguage': 'nb-NO',
         'publisher': {'@id': URL + '#org'}},
    ],
}

ICON_IG = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/>'
           '<circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>')
ICON_STACK = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
              'stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="7" width="14" height="14" rx="2"/>'
              '<path d="M3 17V5a2 2 0 0 1 2-2h12"/></svg>')
CHEV = {-1: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
        1: '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>'}


def version(f):
    return hashlib.md5(open(f'{SITE}/{f}', 'rb').read()).hexdigest()[:8]


def photo(b, alt, sizes, eager=False, large=False, cls=''):
    w, h = dims(b)
    srcset = f'img/{b}-s.webp 480w, img/{b}-m.webp 900w' + (f', img/{b}-l.webp 1440w' if large else '')
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="img/{b}-m.webp" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{E(alt)}"{load} decoding="async">')


def cut_label(p, cut):
    return dict(p['img'])[cut]


def studio_alt(p, cut, color, view):
    if view == 'life':
        return f"{p['name']} fra Frostline på modell"
    lab = cut_label(p, cut)
    snitt = f" i {'unisex-snitt' if lab == 'Unisex' else 'damesnitt'}" if lab else ''
    col = dict((c, n) for c, n, _ in COLORS)[color]
    return f"{col} {p['lname']}{snitt} fra Frostline, {'forfra' if view == 'front' else 'bakfra'}"


def stage(p, sizes):
    cut = p['img'][0][0]
    b = f'img/p/{cut}-graa-front'
    segs = ''
    if len(p['img']) > 1:
        segs += ('<div class="seg" data-k="cut" role="group" aria-label="Snitt">' + ''.join(
            f'<button type="button" data-v="{c}" aria-pressed="{str(k == 0).lower()}">{E(l)}</button>'
            for k, (c, l) in enumerate(p['img'])) + '</div>')
    segs += ('<div class="seg" data-k="view" role="group" aria-label="Vis plagget">' + ''.join(
        f'<button type="button" data-v="{v}" aria-pressed="{str(k == 0).lower()}">{l}</button>'
        for k, (v, l) in enumerate((('front', 'Foran'), ('back', 'Bak'), ('life', 'Modell')))) + '</div>')
    sw = ('<div class="swatches" data-k="color" role="group" aria-label="Farge">' + ''.join(
        f'<button type="button" class="sw" data-v="{c}" aria-pressed="{str(k == 0).lower()}" '
        f'aria-label="{E(n)}" title="{E(n)}" style="--c:{hx}"></button>' for k, (c, n, hx) in enumerate(COLORS))
          + '</div>')
    return (f'<div class="stage"><img src="{b}-1000.webp" srcset="{b}-600.webp 600w, {b}-1000.webp 1000w" '
            f'sizes="{sizes}" width="1000" height="1000" alt="{E(studio_alt(p, cut, "graa", "front"))}" '
            f'loading="lazy" decoding="async"></div>'
            f'<div class="ctrl">{segs}{sw}</div>')


def rail(p, pi):
    n = len(p['worn_imgs'])
    tiles = ''.join(
        f'<button class="tile" type="button" data-s="p{pi}" data-i="{k}" aria-label="{E(im["g"])}, bilde {k + 1} av {n}">'
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


def head(style, preview):
    robots = '<meta name="robots" content="noindex">\n' if preview else ''
    return f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{E(DESC)}">
{robots}<link rel="canonical" href="{URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Frostline">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{E(DESC)}">
<meta property="og:image" content="{URL}assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{URL}">
<meta property="og:locale" content="nb_NO">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#09090b">
<link rel="icon" href="assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,500;9..40,700;9..40,800&family=Graduate&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css?v={version('style.css')}">
<link rel="stylesheet" href="v-{style}.css?v={version(f'v-{style}.css')}">
<script type="application/ld+json">{json.dumps(LD, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body class="v-{style}">
<a class="skip" href="#produkter">Hopp til plaggene</a>
<header class="bar"><div class="bar-in">
<a class="bar-logo" href="#top" aria-label="Frostline, til toppen"><img src="assets/frostline-logo-white.png" alt="Frostline" width="992" height="142"></a>
<a class="dm" href="{DM}" target="_blank" rel="noopener" aria-label="Send oss en DM på Instagram">{ICON_IG}<span>DM</span></a>
</div></header>
'''


def tail():
    return f'''<section class="ig" id="kontakt" aria-labelledby="ig-h">
<h2 class="sr" id="ig-h">Kontakt oss på Instagram</h2>
<a class="handle" href="{IG}" target="_blank" rel="noopener">@frostlineno</a>
<a class="btn" href="{DM}" target="_blank" rel="noopener" aria-label="Send oss en DM på Instagram">{ICON_IG}<span>DM</span></a>
</section>
</main>
<footer class="foot">
<img src="assets/frostline-logo-white.png" alt="" width="992" height="142" loading="lazy">
<p>Frostec AS · Org.nr 930 093 777</p>
</footer>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Bildevisning">
<button class="lb-close" type="button" aria-label="Lukk">&times;</button>
<button class="lb-prev" type="button" aria-label="Forrige">&#8249;</button>
<button class="lb-next" type="button" aria-label="Neste">&#8250;</button>
<figure class="lb-fig"><img id="lb-img" alt=""><figcaption id="lb-cap"></figcaption></figure>
</div>
<script id="data" type="application/json">{json.dumps(DATA, ensure_ascii=False, separators=(',', ':'))}</script>
<script src="app.js?v={version('app.js')}"></script>
</body>
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


def lineup():
    items = []
    for p in PRODUCTS:
        pid = p['id']
        w, h = Image.open(f'{SITE}/img/p/lineup-{pid}.webp').size
        items.append(f'<a href="#{pid}"><img src="img/p/lineup-{pid}.webp" alt="" width="{w}" height="{h}" '
                     f'fetchpriority="high"><span>{E(p["name"])}</span></a>')
    return '<nav class="lineup" aria-label="Plaggene">' + ''.join(items) + '</nav>'


# ---------------------------------------------------------------- a: Lookbook
def body_a():
    arts = []
    for pi, p in enumerate(PRODUCTS):
        arts.append(f'''<article class="product{' flip' if pi % 2 else ''}" id="{p['id']}" data-p="{pi}">
<div class="p-media">{stage(p, '(min-width: 960px) 560px, 100vw')}</div>
<div class="p-info">
<p class="p-num">0{pi + 1}<span> / 0{len(PRODUCTS)}</span></p>
<h3 class="p-name">{E(p['name'])}</h3>
</div>
{rail(p, pi)}
</article>''')
    return f'''<main>
<section class="hero" id="top">
{logo_h1()}
{lineup()}
</section>
<section class="products" id="produkter" aria-labelledby="p-h">
<div class="wrap">
<h2 class="sr" id="p-h">Plaggene</h2>
{''.join(arts)}
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


def body_b():
    mw, mh = mosaic()
    panels = []
    for pi, p in enumerate(PRODUCTS):
        feat = p['worn_imgs'][0]
        n = len(p['worn_imgs'])
        panels.append(f'''<article class="panel{' flip' if pi % 2 else ''}" id="{p['id']}" data-p="{pi}">
<button class="panel-photo" type="button" data-s="p{pi}" data-i="0" aria-label="Se {n} bilder av {E(p['lname'])} på russen">
{photo(feat['b'], f"Russegruppa {feat['g']} i {p['lname']} fra Frostline", '(min-width: 900px) 50vw, 100vw', large=True)}
<span class="panel-credit">{E(feat['g'])}</span>
<span class="panel-count" aria-hidden="true">{ICON_STACK}{n}</span>
</button>
<div class="panel-body">
<p class="p-num">0{pi + 1}<span> / 0{len(PRODUCTS)}</span></p>
<h3 class="panel-name">{E(p['name'])}</h3>
<div class="panel-studio">{stage(p, '(min-width: 900px) 380px, 100vw')}</div>
</div>
</article>''')
    return f'''<main>
<section class="hero hero-b" id="top">
<img class="hero-bg" src="assets/mosaic.jpg" alt="" width="{mw}" height="{mh}" fetchpriority="high">
<div class="hero-in">
{logo_h1()}
</div>
<a class="scroll-cue" href="#produkter" aria-label="Til plaggene"><span></span></a>
</section>
<section class="panels" id="produkter" aria-labelledby="p-h">
<h2 class="sr" id="p-h">Plaggene</h2>
{''.join(panels)}
</section>
{marquee()}
<section class="groups-b" id="grupper" aria-labelledby="g-h">
<h2 class="sr" id="g-h">Russegruppene</h2>
<ul class="wall">{group_cards('(min-width: 1280px) 15vw, (min-width: 720px) 25vw, 50vw', 'wcard')}</ul>
</section>
'''


# ---------------------------------------------------------------- c: Indeks
def studio_strip(p):
    shots = []
    for cut, lab in p['img']:
        views = (('graa', 'front'), ('navy', 'front')) if len(p['img']) > 1 else (('graa', 'front'), ('graa', 'back'), ('navy', 'front'), ('navy', 'back'))
        for col, v in views:
            shots.append((cut, col, v))
    return '<div class="studio">' + ''.join(
        f'<figure class="stage"><img src="img/p/{c}-{col}-{v}-600.webp" width="600" height="600" '
        f'alt="{E(studio_alt(p, c, col, v))}" loading="lazy" decoding="async"></figure>' for c, col, v in shots) + '</div>'


def body_c():
    rows = []
    for pi, p in enumerate(PRODUCTS):
        w, h = Image.open(f'{SITE}/img/p/lineup-{p["id"]}.webp').size
        rows.append(f'''<details class="row" id="{p['id']}" data-p="{pi}">
<summary><span class="row-num">0{pi + 1}</span><span class="row-name">{E(p['name'])}</span><span class="row-plus" aria-hidden="true"></span>
<img class="row-peek" src="img/p/lineup-{p['id']}.webp" alt="" width="{w}" height="{h}" loading="lazy"></summary>
<div class="row-body">
{studio_strip(p)}
{rail(p, pi)}
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
<h2 class="sr" id="i-h">Plaggene</h2>
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


BODIES = {'a': body_a, 'b': body_b, 'c': body_c}


def page(style, preview=False):
    return head(style, preview) + BODIES[style]() + tail()


for s in STYLES:
    open(f'{SITE}/preview-{s}.html', 'w').write(page(s, preview=True))
live = page(site['live'])
open(f'{SITE}/index.html', 'w').write(live)

today = datetime.date.today().isoformat()
open(f'{SITE}/sitemap.xml', 'w').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f'<url><loc>{URL}</loc><lastmod>{today}</lastmod></url>\n</urlset>\n')
open(f'{SITE}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /_source/\nDisallow: /preview-\nSitemap: {URL}sitemap.xml\n')

n_imgs = sum(len(g['imgs']) for g in GROUPS)
print(f"live style {site['live']}, groups {N_GROUPS}, group photos {n_imgs}, "
      f"product photos {sum(len(p['worn']) for p in PRODUCTS)}, index.html {len(live)} bytes")
