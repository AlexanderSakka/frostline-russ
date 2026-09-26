"""Build the site from the JSON files in _source/.

  python3 _source/build.py              # index.html in the live style, plus the three previews
  python3 _source/build.py --live b     # make style b the live one (saved in site.json)

Three styles share the same data, images, style.css and app.js:
  a  Lookbook   the logo, then every garment as a tile that turns into a group wearing it
  b  Kampanje   a wall of group photos behind the logo, the garments as one big swipeable strip
  c  Indeks     a black index you open garment by garment, the groups as a name list

Each garment opens a lightbox: its model photo(s) first, then the groups wearing it.
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

# lightbox sets: p<i> is a garment (model photos, then the groups in it), g<i> a group
DATA = {'s': {}}
for i, p in enumerate(PRODUCTS):
    model = [{'s': f'img/p/{pid}-model-1000.webp', 'w': 1000, 'h': 1000, 'c': cut} for pid, cut in p['photos']]  # stamped below
    DATA['s'][f'p{i}'] = {'t': p['name'], 'k': 'p', 'imgs': model + p['worn_imgs']}
for i, g in enumerate(GROUPS):
    DATA['s'][f'g{i}'] = {'t': g['name'], 'k': 'g', 'imgs': g['imgs']}

TITLE = 'Frostline | Russeklær for russegrupper'
DESC = ('Frostline lager russeklær for russegrupper: zip hoodie, hoodie, crewneck, bukse, shorts, '
        't-skjorte, longsleeve, singlet og collegejakke med gruppas eget trykk. Kontakt oss på Instagram.')
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
<h2 class="sr" id="p-h">Plaggene</h2>
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


def body_b():
    mw, mh = mosaic()
    sizes = '(min-width: 1100px) 30vw, (min-width: 640px) 44vw, 78vw'
    slides = ''.join(
        f'<article class="slide" id="{p["id"]}">'
        f'<button class="slide-photo shot" type="button" data-s="p{pi}" data-i="0" aria-label="{E(open_label(p))}">'
        f'{model_img(p, 0, sizes)}{second_look(p, sizes)}{count(p)}</button>'
        f'<p class="p-num">{pi + 1:02d}<span> / {len(PRODUCTS):02d}</span></p>'
        f'<h3 class="slide-name">{E(p["name"])}</h3></article>'
        for pi, p in enumerate(PRODUCTS))
    arrows = ''.join(f'<button class="arr" type="button" data-dir="{d}" aria-label="{"Forrige" if d < 0 else "Neste"} plagg">{CHEV[d]}</button>' for d in (-1, 1))
    return f'''<main>
<section class="hero hero-b" id="top">
<img class="hero-bg" src="assets/mosaic.jpg" alt="" width="{mw}" height="{mh}" fetchpriority="high">
<div class="hero-in">
{logo_h1()}
</div>
<a class="scroll-cue" href="#produkter" aria-label="Til plaggene"><span></span></a>
</section>
<section class="strip-sec worn" id="produkter" aria-labelledby="p-h">
<h2 class="sr" id="p-h">Plaggene</h2>
<div class="wrap strip-head"><div class="arrows">{arrows}</div></div>
<div class="rail strip">{slides}</div>
</section>
{marquee()}
<section class="groups-b" id="grupper" aria-labelledby="g-h">
<h2 class="sr" id="g-h">Russegruppene</h2>
<ul class="wall">{group_cards('(min-width: 1280px) 15vw, (min-width: 720px) 25vw, 50vw', 'wcard')}</ul>
</section>
'''


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


for st in DATA['s'].values():
    for im in st['imgs']:
        if 's' in im and '?v=' not in im['s']:
            im['s'] += f"?v={version(im['s'])}"

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
print(f"live style {site['live']}, garments {len(PRODUCTS)}, groups {N_GROUPS}, group photos {n_imgs}, "
      f"garment photos {sum(len(p['worn']) for p in PRODUCTS)}, index.html {len(live)} bytes")
