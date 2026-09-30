"""The addresses that only send you on to this site: russ.frostlinenorge.no, which it left for
frostlinenorge.no on 2026-09-29 (the skoleklær store moved from there to skole.frostlinenorge.no).

GitHub Pages gives a repository one custom domain, so each is held by its own tiny repository,
checked out beside this one ("aliases" in site.json; russ is AlexanderSakka/frostline-russ-redirect).
www.frostlinenorge.no cannot be one: GitHub reserves it for the repository holding the bare
domain and redirects it there itself. Each alias sends every address on to the same path here:
  - the front page, each garment page and the published styles get a page of their own with
    the real page's title and link preview, which goes on at once keeping the ?query and the
    #colour (hoodie#navy), and with a 0-second refresh when JavaScript is off (search engines
    read that as a permanent move);
  - anything else (a photo, a mistyped path, a store link) goes on through 404.html, path and all;
  - the icons are copied (favicon.ico, assets/favicon.png, assets/apple-touch-icon.png) and linked
    as on the real pages, so a search result that still lists this address shows the F and not
    a globe (Google takes the icon per host, from the host's own front page).

  python3 _source/build.py && python3 _source/moved.py
  then in ../frostline-russ-redirect: git add -A && git commit -m "..." && git push

Run it again when a garment is added or renamed or a style is published. CNAME in each holds its
host, and its Pages settings have it too, with HTTPS enforced.
"""
import json, os, re, html, shutil

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
E = html.escape
site = json.load(open(f'{S}/site.json'))
NEW = f"https://{site['domain']}/"
BODY = 'margin:0;padding:32px 16px;background:#09090b;font:600 16px/1.5 system-ui,sans-serif'
ICONS = ('favicon.ico', 'assets/favicon.png', 'assets/apple-touch-icon.png')
OG = ('og:type', 'og:site_name', 'og:title', 'og:description', 'og:image', 'og:image:width',
      'og:image:height', 'og:locale')


def meta(h, key):
    m = re.search(r'<meta (?:property|name)="' + re.escape(key) + r'" content="([^"]*)">', h)
    return m.group(1) if m else ''


def forward(page, to):
    """The page at the other address: the real page's title, description and link preview (the
    values are copied as they stand, already escaped), then on to the real one."""
    h = open(f'{SITE}/{page}').read()
    title = re.search(r'<title>(.*?)</title>', h).group(1)
    og = ''.join(f'<meta property="{k}" content="{meta(h, k)}">\n' for k in OG if meta(h, k))
    icons = ''.join(t + '\n' for t in re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*>', h))
    return f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta(h, 'description')}">
<link rel="canonical" href="{E(to)}">
{icons}{og}<meta property="og:url" content="{E(to)}">
<meta name="twitter:card" content="summary_large_image">
<script>location.replace({json.dumps(to)}+location.search+location.hash)</script>
<noscript><meta http-equiv="refresh" content="0; url={E(to)}"></noscript>
</head>
<body style="{BODY}">
<a href="{E(to)}" style="color:#fff">{E(to.split('//')[1].rstrip('/'))}</a>
</body>
</html>
'''


NOT_FOUND = f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Frostline</title>
<script>location.replace({json.dumps(NEW.rstrip('/'))}+location.pathname+location.search+location.hash)</script>
<noscript><meta http-equiv="refresh" content="0; url={E(NEW)}"></noscript>
</head>
<body style="{BODY}">
<a href="{E(NEW)}" style="color:#fff">{E(NEW.split('//')[1].rstrip('/'))}</a>
</body>
</html>
'''


def write(host, out):
    os.makedirs(out, exist_ok=True)
    pages = {'index.html': NEW}
    for p in json.load(open(f'{S}/products.json'))['products']:
        pages[f"{p['id']}.html"] = NEW + p['id']
    for s in site.get('published', []):
        pages[f'{s}.html'] = NEW + s
    for f in os.listdir(out):
        if f.endswith('.html') and f not in pages and f != '404.html':
            os.remove(f'{out}/{f}')
    for f, to in pages.items():
        open(f'{out}/{f}', 'w').write(forward(f, to))
    open(f'{out}/404.html', 'w').write(NOT_FOUND)
    os.makedirs(f'{out}/assets', exist_ok=True)
    for f in ICONS:
        shutil.copyfile(f'{SITE}/{f}', f'{out}/{f}')
    open(f'{out}/CNAME', 'w').write(host + '\n')
    open(f'{out}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {NEW}sitemap.xml\n')
    open(f'{out}/.nojekyll', 'w').write('')
    open(f'{out}/README.md', 'w').write(f'''# {host}

An address of Frostline's russ site at {NEW}. This repository only holds {host} (GitHub
Pages gives each repository one domain) and sends every address on to the same path there. It
is written by `_source/moved.py` in AlexanderSakka/frostline-russ; do not edit it by hand.
''')
    print(f'{host} -> {NEW}: {len(pages)} pages + 404.html in {out}')


for host, repo in site['aliases'].items():
    write(host, os.path.join(os.path.dirname(SITE), repo))
