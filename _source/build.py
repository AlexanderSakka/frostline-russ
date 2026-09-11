import json, os, html
from PIL import Image
S=os.path.dirname(os.path.abspath(__file__))
SITE=os.path.dirname(S)
posts={p['n']:p for p in json.load(open(f'{S}/posts.json'))}
groups=json.load(open(f'{S}/groups.json'))
HERO='04-1'
def dims(base):
    im=Image.open(f'{SITE}/img/{base}-m.webp'); return im.size
data=[]
for g in groups:
    files=[]
    for n in [g['n']]+g.get('also',[]):
        files+=[i['file'][:-4] for i in posts[n]['images'] if i['ok']]
    order=[g['cover']]+[f for f in files if f!=g['cover'] and f!=HERO]
    imgs=[]
    for f in order:
        w,h=dims(f); imgs.append({'b':f,'w':w,'h':h})
    data.append({'name':g['name'],'handle':g['handle'],'imgs':imgs})
n_groups=len(data); n_imgs=sum(len(d['imgs']) for d in data)
E=html.escape
cards=[]
for gi,g in enumerate(data):
    cov=g['imgs'][0]; extras=g['imgs'][1:]
    alt=E(f"Russegruppa {g['name']} i klær fra Frostline")
    handle=''
    eager='' if gi>1 else ' fetchpriority="high"'
    lazy=' loading="lazy"' if gi>1 else ''
    thumbs=''
    if extras:
        show=extras[:4]; more=len(extras)-len(show)
        t=[]
        for k,im in enumerate(show):
            plus=f'<span class="more">+{more}</span>' if (more and k==len(show)-1) else ''
            t.append(f'<button class="thumb" type="button" data-g="{gi}" data-i="{k+1}" aria-label="Bilde {k+2} av {len(g["imgs"])}, {E(g["name"])}"><img src="img/{im["b"]}-m.webp" width="{im["w"]}" height="{im["h"]}" alt="" loading="lazy" decoding="async">{plus}</button>')
        thumbs=f'<div class="thumbs">{"".join(t)}</div>'
    cards.append(f'''<article class="card">
<button class="cover" type="button" data-g="{gi}" data-i="0" aria-label="Åpne bilder av {E(g['name'])}">
<img src="img/{cov['b']}-m.webp" width="{cov['w']}" height="{cov['h']}" alt="{alt}"{lazy}{eager} decoding="async">
<span class="label"><span class="name">{E(g['name'])}</span>{handle}</span>
</button>{thumbs}</article>''')
hw,hh=dims(HERO)
page=f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Russegrupper | Frostline</title>
<meta name="description" content="Se russegruppene Frostline har levert gruppeklær til: hoodies, gensere, bukser og t-skjorter med gruppas eget design.">
<link rel="canonical" href="https://russ.frostlinenorge.no/">
<meta property="og:type" content="website">
<meta property="og:title" content="Russegrupper Frostline har kledd opp">
<meta property="og:description" content="{n_groups} russegrupper, {n_imgs} bilder. Gruppeklær med eget design fra Frostline.">
<meta property="og:image" content="https://russ.frostlinenorge.no/img/{HERO}-l.webp">
<meta property="og:url" content="https://russ.frostlinenorge.no/">
<meta property="og:locale" content="nb_NO">
<meta name="theme-color" content="#0b0b0d">
<link rel="icon" href="assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,500;9..40,700;9..40,800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
<a href="https://frostlinenorge.no" class="logo" aria-label="Frostline"><img src="assets/frostline-logo-white.png" alt="FROSTLINE" width="992" height="142"></a>
<a class="ig" href="https://www.instagram.com/frostlineno/" target="_blank" rel="noopener">@frostlineno</a>
</header>

<section class="hero">
<img src="img/{HERO}-l.webp" width="{hw}" height="{hh}" alt="Fly med banner: Frostline x Daskeladden" fetchpriority="high" decoding="async">
</section>

<h1 class="sr">Russegrupper Frostline har levert til</h1>
<main class="grid" id="grupper">
{"".join(cards)}
</main>

<section class="cta" id="kontakt">
<a class="button" href="mailto:post@frostlinenorge.no?subject=Russekl%C3%A6r%20til%20gruppa%20v%C3%A5r">Kontakt oss</a>
</section>

<footer>
<p><a href="https://frostlinenorge.no">frostlinenorge.no</a></p>
</footer>

<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Bildevisning">
<button class="lb-close" type="button" aria-label="Lukk">&times;</button>
<button class="lb-prev" type="button" aria-label="Forrige">&#8249;</button>
<button class="lb-next" type="button" aria-label="Neste">&#8250;</button>
<figure class="lb-fig"><img id="lb-img" alt=""><figcaption id="lb-cap"></figcaption></figure>
</div>
<script id="data" type="application/json">{json.dumps(data,ensure_ascii=False,separators=(",",":"))}</script>
<script src="app.js"></script>
</body>
</html>
'''
open(f'{SITE}/index.html','w').write(page)
print('groups',n_groups,'images',n_imgs,'html bytes',len(page))
