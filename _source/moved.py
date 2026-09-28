"""The site's old address, russ.frostlinenorge.no, which it left for frostlinenorge.no on
2026-09-28 (the skoleklær store moved from there to skole.frostlinenorge.no the same day).

GitHub Pages gives a repository one custom domain, so the old address is held by a second, tiny
repository, AlexanderSakka/frostline-russ-redirect, checked out beside this one at
../frostline-russ-redirect. It sends every address on to the same path on the new domain:
  - the front page, each garment page and the published styles get a page of their own with
    the real page's title and link preview, which goes on at once keeping the ?query and the
    #colour (hoodie#navy), and with a 0-second refresh when JavaScript is off (search engines
    read that as a permanent move);
  - anything else (a photo, a mistyped path) goes on through 404.html, path and all.

  python3 _source/build.py && python3 _source/moved.py
  cd ../frostline-russ-redirect && git add -A && git commit -m "..." && git push

Run it again when a garment is added or renamed or a style is published. CNAME there holds the
old domain; the redirect repository's Pages settings have it too, with HTTPS enforced.
"""
import json, os, re, html

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
OUT = os.path.join(os.path.dirname(SITE), 'frostline-russ-redirect')
E = html.escape
site = json.load(open(f'{S}/site.json'))
OLD, NEW = site['moved_from'], f"https://{site['domain']}/"
BODY = 'margin:0;padding:32px 16px;background:#09090b;font:600 16px/1.5 system-ui,sans-serif'
OG = ('og:type', 'og:site_name', 'og:title', 'og:description', 'og:image', 'og:image:width',
      'og:image:height', 'og:locale')


def meta(h, key):
    m = re.search(r'<meta (?:property|name)="' + re.escape(key) + r'" content="([^"]*)">', h)
    return m.group(1) if m else ''


def forward(page, to):
    """The page at the old address: the real page's title, description and link preview (the
    values are copied as they stand, already escaped), then on to the new address."""
    h = open(f'{SITE}/{page}').read()
    title = re.search(r'<title>(.*?)</title>', h).group(1)
    og = ''.join(f'<meta property="{k}" content="{meta(h, k)}">\n' for k in OG if meta(h, k))
    return f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta(h, 'description')}">
<link rel="canonical" href="{E(to)}">
{og}<meta property="og:url" content="{E(to)}">
<meta name="twitter:card" content="summary_large_image">
<script>location.replace({json.dumps(to)}+location.search+location.hash)</script>
<noscript><meta http-equiv="refresh" content="0; url={E(to)}"></noscript>
</head>
<body style="{BODY}">
<a href="{E(to)}" style="color:#fff">{E(to.split('//')[1].rstrip('/'))}</a>
</body>
</html>
'''


os.makedirs(OUT, exist_ok=True)
pages = {'index.html': NEW}
for p in json.load(open(f'{S}/products.json'))['products']:
    pages[f"{p['id']}.html"] = NEW + p['id']
for s in site.get('published', []):
    pages[f'{s}.html'] = NEW + s
for f in os.listdir(OUT):
    if f.endswith('.html') and f not in pages and f != '404.html':
        os.remove(f'{OUT}/{f}')
for f, to in pages.items():
    open(f'{OUT}/{f}', 'w').write(forward(f, to))
open(f'{OUT}/404.html', 'w').write(f'''<!DOCTYPE html>
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
''')
open(f'{OUT}/CNAME', 'w').write(OLD + '\n')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nSitemap: {NEW}sitemap.xml\n')
open(f'{OUT}/.nojekyll', 'w').write('')
open(f'{OUT}/README.md', 'w').write(f'''# {OLD}

The old address of Frostline's russ site, which moved to {NEW} on 2026-09-28. This repository
only holds the old domain (GitHub Pages gives each repository one) and sends every address on
to the same path on the new one. It is written by `_source/moved.py` in
AlexanderSakka/frostline-russ; do not edit it by hand.
''')
print(f'{OLD} -> {NEW}: {len(pages)} pages + 404.html in {OUT}')
