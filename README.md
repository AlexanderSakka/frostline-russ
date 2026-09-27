# russ.frostlinenorge.no

Frostline's showcase for russegrupper: every garment a group can order first (zip hoodie,
hoodie, crewneck, bukse, shorts, t-skjorte, longsleeve, singlet, collegejakke) as a product
card that opens the garment's own page, then the custom pieces, then the groups themselves.
No shop, no prices, no email and almost no text on purpose; the only way in is a DM to
@frostlineno.

Hosted on GitHub Pages from `main`; `CNAME` pins the custom domain (written by the build from `site.json`). `index.html` is
generated, never edit it by hand.

## Files

- `index.html`: the page, written by `_source/build.py`.
- `<id>.html` (`zip-hoodie.html`, `hoodie.html`, ...): each garment's own page, also written by
  `build.py`, served as russ.frostlinenorge.no/hoodie. `shop.css` + `pp.js` are theirs (the
  cards on the front page use `shop.css` too).
- `style.css` + `app.js`: shared by every style. `v-a.css`, `v-b.css`, `v-c.css`: the three styles.
- `img/shop/<id>[-<cut>]-<colour>-<front|back>-{600,1200}.webp`: the product photos, cut out of
  their white ground (transparent), and `<first front>-og.jpg` for each page's link preview
  (`make_shop_images.py`).
- `img/<post>-<slide>-{s,m,l}.webp`: Instagram photos at 480, 900 and 1440 px.
- `img/p/<id>-model-{600,1000}.webp`: one on-model photo per garment (two for the cuts of
  bukse and shorts).
- `img/logo/<post>.webp`: each group's chest logo for style b's ticker (`make_logos.py`).
- `img/c/<name>-{s,m,l}.webp`: the custom pieces (`custom.json`).
- `assets/`: logos, `og.jpg` (link preview), `mosaic.jpg` (style b's hero).
- `_source/`: data and scripts (below). Gitignored there: `raw/` (Instagram originals and
  `raw/custom/`), `logo-src/` (the groups' print files, up to 37 MB each),
  `model-photos/` (full-size model photos), `model-refs/` (factory photos used as references;
  they show other groups' designs, keep them off the web).

## The three styles

`_source/site.json` says which one is live (`"live"`) and which are also published on the
domain for comparison (`"published"`, written as `a.html` and `b.html`, so
russ.frostlinenorge.no/a and /b; noindex, canonical to the front page). All three are also
built as `preview-a.html`, `preview-b.html`, `preview-c.html` for local use (gitignored):

- **a, Lookbook**: the logo, then every garment as a tile; hovering a tile turns the model
  photo into a group wearing it. Then the name ticker and the groups in black and white.
- **b, Kampanje** (live): a wall of the groups behind the logo with the groups' own chest
  logos running underneath, each in its own dark tile (each opens that group's photos); the
  garments as dark product cards you swipe or pick by name (the garment floating on a soft
  light, the name in Varsity, a dot per colour: pointing at a dot shows that colour, clicking
  opens the page in it); the custom pieces; the groups edge to edge.
- **c, Indeks**: black and closed, the garments as an index you open one by one, the groups
  as a name list whose photo follows the pointer.

In a and c, clicking a garment opens its model photo(s) first, then the groups wearing it.
In b it opens the garment's page: the product photos (front, back, on a model) in the colour
and cut picked beside them (a link can pick them: `hoodie#navy`, `bukse#dame-svart`), the
name in Varsity, "Farge", for the hoodie and zip hoodie (`"navn": true` in products.json) an
Etternavn field that draws the name on the back photo as it is typed (Bebas Neue, the print
font, in the school store's print box; white on navy and black), the DM; then the groups
wearing it (lightbox), then the other garments.

```
python3 _source/build.py            # rebuild index.html, the garment pages and the previews
python3 _source/build.py --live b   # switch the live style
python3 _source/serve.py            # then open http://127.0.0.1:8765/preview-b.html (serves /hoodie like Pages does)
```

## Data

- `_source/products.json`: the garments in page order, their model photos, and which
  Instagram photos show each one (`worn`, best first).
- `_source/groups.json`: one row per group card (name, handle, cover, extra posts in `also`).
- `_source/posts.json`: captions and image list per Instagram post.
- `_source/logos.json`: where each group's logo came from. Mostly the zip hoodie's front
  chest print from that group's order in the print system (s3://ftmerch-eu-north-1); the
  orders there carry code names, not the group names (Death Row is `westside`, Red Army
  is `siberia`, Doomsday is `czarface`, Glitch is `normandie`...), so every match was made
  by looking at the print. Kodiak and Siberia (autumn 2025, before the print system) have
  no file yet and are left out of the ticker.
- `_source/custom.json`: one-off pieces made for a single group (group, what it is, photos).

## Changing things

- **Swap a photo under a garment**: edit its `worn` list in `products.json`, run `build.py`.
  In style b the first three are the ones on the slide.
- **Add a custom piece**: put the photo in `_source/raw/custom/`, add an entry to
  `custom.json`, run `python3 _source/make_webp.py`, then `build.py`.
- **Add or replace a group logo**: put the print file (transparent PNG) in
  `_source/logo-src/<post>.png`, note its source in `logos.json`, run
  `python3 _source/make_logos.py`, then `build.py`.
- **Add a group**: put the post's images in `_source/raw/` as `<post>-<slide>.jpg`, add a
  `posts.json` entry and a `groups.json` row, run `python3 _source/make_webp.py`, then
  `build.py`.
- **Model photos**: crewneck, bukse, t-skjorte and longsleeve are the skoleklær store's shots
  (`~/skole/assets/skole_*_life.jpg`). The rest are made by `node _source/model_photos.mjs`
  (OpenAI gpt-image-2, key from `~/skole/scripts/.env`, the same model reference as the
  skole shots): hoodie and zip hoodie are the skole shots with russ-length cords, plus
  collegejakke, shorts, singlet and pannebånd. `--dry-run` prints the prompts, `--only a,b`
  redoes some. Then `python3 _source/make_product_images.py` and `build.py`.
- **Product photos** (the cards and garment pages): `python3 _source/make_shop_images.py`
  writes `img/shop/` and `_source/shop.json` (which cuts, colours and views exist). Grey, navy
  and white are the skoleklær store's studio shots (`~/skole/assets/skole_*_{front,back}.jpg`),
  black is made there from the navy, and shorts, singlet and collegejakke come from
  `node _source/product_shots.mjs` (gpt-image-2, our model photo as the garment and a skole shot
  for the look; writes the gitignored `_source/product-shots/`). A new colour or garment is a
  line in its `SOURCES`, then `build.py`. Each photo is cut out of its white ground there.
- **The Varsity names**: product names and the Custom heading are drawn from the Varsity font
  (Brøderbund, 1996, from https://www.dafont.com/varsity-2.font, no licence given) as SVG
  outlines by `_source/varsity.py`; the font file itself is never published. It lives in the
  gitignored `_source/fonts/varsity_regular.ttf` on this Mac; another machine needs it
  downloaded there before `build.py` runs. Needs `fonttools` (and `scipy` for the cutouts).
- **Icons**: `python3 _source/make_icons.py` makes the favicon (the wordmark's F, which
  Google shows beside the site name) and the home-screen icon.

Commit and push; Pages redeploys in about a minute.

## Search engines

The page says almost nothing on purpose, so search engines are told who Frostline is in
places visitors do not see: the meta description, JSON-LD in the head (Organization
"Frostline", also "Frostline Norge", Frostec AS, the Instagram account and the skoleklær
store as `sameAs`, plus WebSite and WebPage), the hidden section headings ("Russeklær",
"Russegruppene") and the photos' alt texts ("Russegruppa X i zip hoodie fra Frostline").
`sitemap.xml` lists the front page and every garment page with every described photo on
them; `robots.txt` points to it. The front page's `<title>` and `og:title` stay the bare
name; a garment page is "Hoodie | Frostline" with its own description, canonical, link
preview and a BreadcrumbList.

`_source/site.json` holds the addresses: `"domain"` (written to `CNAME` and used for
canonical, og and sitemap URLs), `"skole"` (the skoleklær store) and `"forward"`. With
`"forward": true` the build writes a `404.html` that sends any path this site does not
have on to the skoleklær store at the same path; that is for the day this site takes over
frostlinenorge.no and the store moves to a subdomain, so its old links and `/<school>`
short links keep working.

Bing, Yandex and the other IndexNow engines are told about a change with
`curl "https://api.indexnow.org/indexnow?url=https://<domain>/&key=7aa21beeb74799d3de6a9380911714d5"`; the key file is
`7aa21beeb74799d3de6a9380911714d5.txt` at the root.

Search Console: a Domain property for frostlinenorge.no, verified 2026-09-26 with a TXT record
at Domene.no (keep it), covers the apex and every subdomain; the sitemaps are submitted
there and in Bing Webmaster Tools.
