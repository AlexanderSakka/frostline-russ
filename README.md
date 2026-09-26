# russ.frostlinenorge.no

Frostline's showcase for russegrupper: every garment a group can order first (zip hoodie,
hoodie, crewneck, collegejakke, bukse, shorts, t-skjorte, longsleeve, singlet, pannebånd),
each on a model and then on the groups that wear it, then the groups themselves. No shop,
no email and almost no text on purpose; the only way in is a DM to @frostlineno.

Hosted on GitHub Pages from `main`; `CNAME` pins the custom domain. `index.html` is
generated, never edit it by hand.

## Files

- `index.html`: the page, written by `_source/build.py`.
- `style.css` + `app.js`: shared by every style. `v-a.css`, `v-b.css`, `v-c.css`: the three styles.
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
- **b, Kampanje**: a wall of the groups behind the logo with the groups' own chest logos
  running underneath (each opens that group's photos); the garments as slides you swipe
  sideways or pick by name (a group wearing it, the outlined varsity name and the model
  photo, then two more groups); the groups edge to edge; the custom pieces last.
- **c, Indeks**: black and closed, the garments as an index you open one by one, the groups
  as a name list whose photo follows the pointer.

Clicking a garment anywhere opens its model photo(s) first, then the groups wearing it.

```
python3 _source/build.py            # rebuild index.html and the previews
python3 _source/build.py --live b   # switch the live style
python3 -m http.server 8765         # then open http://localhost:8765/preview-a.html
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

Commit and push; Pages redeploys in about a minute.
