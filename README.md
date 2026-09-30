# frostlinenorge.no

Frostline's showcase for russegrupper: every garment a group can order first (zip hoodie,
hoodie, crewneck, bukse, shorts, t-skjorte, longsleeve, singlet, collegejakke) as a product
card that opens the garment's own page, then the custom pieces, then the groups themselves,
and a size guide at frostlinenorge.no/storrelser (since 2026-09-30, Alexander's ask).
No shop, no prices, no email and almost no text on purpose; the only way in is a DM to
@frostlineno. Until 2026-09-29 it lived at russ.frostlinenorge.no and the skoleklær store had
frostlinenorge.no; that day they swapped (the store is now skole.frostlinenorge.no), see
"Addresses" below.

Hosted on GitHub Pages from `main`; `CNAME` pins the custom domain (written by the build from `site.json`). `index.html` is
generated, never edit it by hand.

## Files

- `index.html`: the page, written by `_source/build.py`.
- `<id>.html` (`zip-hoodie.html`, `hoodie.html`, ...): each garment's own page, also written by
  `build.py`, served as frostlinenorge.no/hoodie. `shop.css` + `pp.js` are theirs (the
  cards on the front page use `shop.css` too).
- `storrelser.html`: the size guide, one garment at a time (frostlinenorge.no/storrelser;
  `#bukse` opens one). Bukse and shorts show both cuts at once: the pair picture with each
  cut labelled, one table with a Herre and a Dame part. The same panel opens in a sheet from
  the Størrelser link on each garment page, and the footer links it. `sizes.css` + `sizes.js`.
- `style.css` + `app.js`: shared by every style. `v-a.css`, `v-b.css`, `v-c.css`: the three styles.
- `img/shop/<id>[-<cut>]-<colour>-<front|back>-{600,1200}.webp`: the product photos, cut out of
  their white ground (transparent), and `<first front>-og.jpg` for each page's link preview
  (`make_shop_images.py`); `-200.webp` copies for the size guide's row of garments, made by
  `build.py` itself.
- `img/shop/<bukse|shorts>-pair-<colour>-{600,1200}.webp`: both cuts (herre, dame) side by
  side at one scale, made by `build.py` (`pair_images`) from the photos above: the front-page
  cards and the size guide show these, so the women's cut is seen without opening anything.
- `img/<post>-<slide>-{s,m,l}.webp`: Instagram photos at 480, 900 and 1440 px.
- `img/p/<id>-model-{600,1000}.webp`: one on-model photo per garment (two for the cuts of
  bukse and shorts).
- `img/logo/<post>.webp`: each group's chest logo for style b's ticker (`make_logos.py`).
- `img/c/<name>-{s,m,l}.webp`: the custom pieces (`custom.json`).
- `404.html`, `lorenskog.html`, `lørenskog.html`, `demo.html`: the school store's old links,
  sent on to skole.frostlinenorge.no (see "Addresses").
- `cdn/shop/t/2/assets/`: the e-mail signature logos, kept at the paths the store served them
  from, because signatures and sent e-mails load them from frostlinenorge.no.
- `assets/`: logos, `og.jpg` (link preview), `mosaic.jpg` (style b's hero).
- `_source/`: data and scripts (below). Gitignored there: `raw/` (Instagram originals and
  `raw/custom/`), `logo-src/` (the groups' print files, up to 37 MB each),
  `model-photos/` (full-size model photos), `model-refs/` (factory photos used as references;
  they show other groups' designs, keep them off the web).

## The three styles

`_source/site.json` says which one is live (`"live"`) and which are also published on the
domain for comparison (`"published"`, written as `a.html` and `b.html`, so
frostlinenorge.no/a and /b; noindex, canonical to the front page). All three are also
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
- `_source/custom.json`: one-off pieces made for a single group (group, what it is, photos,
  an alt per photo). Style b shows the photos three across at 4:5 on every screen, the
  group's name on the middle one from 720 px up. Swag's three come from Alexander's Drive
  folder, cut above the FROSTLINE wordmark along their bottom; the note there has the boxes.
- The men's cut of bukse and shorts is called **Herre** on the page (Alexander, 2026-09-30),
  though the order sheets say "Bukse unisex"; the data, the photo files and the #links keep
  the key `unisex`. The name is `CUT_NAME` in `build.py`.
- `_source/sizes.json`: the size guide's numbers per garment and cut, and where each
  measuring line sits on the product photo. Its `_note` says where every number comes from:
  the factory's 2026 spec sheets for the fleece garments, the russ print guide for the
  t-skjorte, longsleeve and singlet (which is the size a group orders, one up from the
  Stanley/Stella and Bella+Canvas blank for the t-shirt and singlet). No collegejakke table:
  the factory never sent one.

## Changing things

- **Swap a photo under a garment**: edit its `worn` list in `products.json`, run `build.py`.
  In style b the first three are the ones on the slide.
- **Add a custom piece**: put its photos in `_source/raw/custom/` cut to 4:5 (three fill a
  row), add an entry to `custom.json`, run `python3 _source/make_webp.py`, then `build.py`.
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
  writes `img/shop/` and `_source/shop.json` (which cuts, colours and views exist). Only the
  colours Frostline sells: grey and navy fleece (shorts too), white jersey, the navy college
  jacket, no black. Grey, navy and white are the skoleklær store's studio shots
  (`~/skole/assets/skole_*_{front,back}.jpg`); shorts, singlet and collegejakke come from
  `node _source/product_shots.mjs` (gpt-image-2, a one-sentence prompt with our model photo as
  the garment and a skole shot for the look; the navy shorts are the grey shot plus a skole
  navy shot for the colour; writes the gitignored `_source/product-shots/`). A
  new colour or garment is a line in its `SOURCES`, then `build.py`. Each photo is cut out of
  its white ground there with a known-background matte (the top of the script explains it),
  so no white rim or white slit between sleeve and body shows on the dark cards, and no dark
  fleck along a grey marl's outline or black line on its cuff and hem seams (both came from
  judging grey against white by absolute numbers; the rules now compare with the fabric
  beside the pixel); it takes about five minutes (`--only hoodie,zip-hoodie` redoes just
  those).
- **Cord length**: the skole shots' drawcords are too long for Frostline's hoodies, so
  `python3 _source/shorten_cords.py` lifts the cord ends on the hoodie and zip hoodie fronts
  (and the hoodie model photo) to the length of the zip hoodie model photo, filling the fabric
  in from beside the cord; run it before `make_shop_images.py` when one of those shots changes.
- **The Varsity names**: product names and the Custom heading are drawn from the Varsity font
  (Brøderbund, 1996, from https://www.dafont.com/varsity-2.font, no licence given) as SVG
  outlines by `_source/varsity.py`; the font file itself is never published. It lives in the
  gitignored `_source/fonts/varsity_regular.ttf` on this Mac; another machine needs it
  downloaded there before `build.py` runs. The font's own Ø is a solid block without the
  outline, so `varsity.py` draws Ø from the font's O (a slash through the counter, the
  outline regrown round it). Needs `fonttools` and `shapely` (the Ø), and `scipy` for the
  cutouts.
- **Icons**: `python3 _source/make_icons.py` makes the favicon (the wordmark's F, which
  Google shows beside the site name) and the home-screen icon.
- **Size guide**: numbers and measuring lines are in `_source/sizes.json`, then `build.py`.
  A measuring line (`mark`) is points in the product photo's 1200 x 1200 pixels, read off
  the cut-out's outline: two points draw a straight line, three bend at the middle one (a
  raglan sleeve from the neck over the shoulder to the cuff); `at` moves its letter along
  the line when it would sit on another line. A new product photo with a different crop
  needs its lines read again. For bukse and shorts the lines are read on each cut's own
  photo and moved onto its half of the pair picture by the build; the same letter must mean
  the same measurement in both cuts (the build stops if not), and a measurement only one cut
  has goes last and shows as a dash in the other. A garment missing from `sizes.json` gets no size guide and no
  Størrelser link (the collegejakke until the factory sends its measurements).

Commit and push; Pages redeploys in about a minute.

## Addresses

`_source/site.json` holds them: `"domain"` (written to `CNAME` and used for canonical, og and
sitemap URLs), `"skole"` (the skoleklær store, also in the JSON-LD `sameAs`), `"forward"`,
`"store_links"` and `"aliases"`.

On 2026-09-29 (early morning, Norwegian time) this site moved from russ.frostlinenorge.no to
frostlinenorge.no, and the Shopify store moved from frostlinenorge.no to
skole.frostlinenorge.no (Shopify admin, Domains: skole is the primary domain; frostlinenorge.no
and www are still listed there, so pointing the DNS back at Shopify would undo the swap at once).
Links made before that keep working:

- **The store's old links** (`"forward": true`): `404.html` sends any path this site does not
  have to the store at the same path, query and #fragment (a product, the cart, the
  order-status link in an order e-mail, `/<school>`), and one of this site's own pages written
  differently (`/Hoodie`, `/hoodie/`) to that page. The school short links the store handed
  out, `"store_links"`, also get a page each (`lorenskog.html`...) that forwards with a
  0-second refresh, so they work without JavaScript and in link previews. A new school needs
  nothing here: its `/<slug>` goes through `404.html`. Pictures cannot be forwarded that way,
  so the e-mail signature logos sit in `cdn/shop/t/2/assets/` as copies of what the store
  served.
- **This site's old address** (`"aliases"`): GitHub Pages gives a repository one custom
  domain, so russ.frostlinenorge.no is held by a second repository,
  AlexanderSakka/frostline-russ-redirect (checked out beside this one), written by
  `python3 _source/moved.py`: a page per garment with that page's link preview that goes on to
  the same page here (keeping `#navy`), and a `404.html` for everything else. Run it and push
  that repository after adding or renaming a garment.
- **www.frostlinenorge.no** is a CNAME to alexandersakka.github.io; GitHub redirects it to the
  bare domain itself and reserves it for this repository (a separate repository for www is
  refused). Over https that needs this site's certificate to cover www too. The first one,
  issued 2026-09-29 a minute before www pointed here, did not, and GitHub kept reusing it
  (removing and re-adding the custom domain got the same one back). What got a new one: switching
  the custom domain to www and back queued a request for both names, which then sat at "new"
  for six hours until the repository's Settings > Pages page was opened in a browser: that runs
  GitHub's DNS check, and the certificate was issued a minute later. So if a certificate hangs at
  "new", open that page first. HTTPS can only be enforced while a certificate is issued, so it
  was off during the wait. Switching the domain to www makes GitHub redirect the bare domain to
  www, and its redirects carry no cache headers, so only do that at night.
  (AlexanderSakka/frostline-www-redirect was made for www before that refusal; Pages is off
  there and it can be deleted.)

DNS (Domene.no cPanel Zone Editor, frostlinenorge.no): the bare domain has GitHub's four A
records (185.199.108-111.153, TTL 300; cPanel insists that records with the same name and type
share one TTL, and there used to be two identical Shopify A records), `www` and `russ` are
CNAMEs to alexandersakka.github.io., `skole` a CNAME to shops.myshopify.com. Mail is separate
and did not move: MX is mail.frostlinenorge.no (its own A record, 185.126.36.19, like webmail,
cpanel and ftp). The network this Mac is often on answers DNS from a cache, even queries sent
straight to ns1/ns2/ns3.dnsdomene.net; to see a change as it lands, ask them through a web dig
(digwebinterface.com with "Specify myself"). `python3 _source/check_addresses.py` checks every
old and new address (resolving through Google's DNS over HTTPS).

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

Bing, Yandex and the other IndexNow engines are told about a change with
`curl "https://api.indexnow.org/indexnow?url=https://<domain>/&key=7aa21beeb74799d3de6a9380911714d5"`; the key file is
`7aa21beeb74799d3de6a9380911714d5.txt` at the root.

Search Console: a Domain property for frostlinenorge.no, verified 2026-09-26 with a TXT record
at Domene.no (keep it), covers the apex and every subdomain; the sitemaps are submitted
there and in Bing Webmaster Tools.
