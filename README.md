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
- `assets/`: logos, `og.jpg` (link preview), `mosaic.jpg` (style b's hero).
- `_source/`: data and scripts (below). Gitignored there: `raw/` (Instagram originals),
  `model-photos/` (full-size model photos), `model-refs/` (factory photos used as references;
  they show other groups' designs, keep them off the web).

## The three styles

`_source/site.json` says which one is live (`"live"`) and which are also published on the
domain for comparison (`"published"`, written as `a.html` and `b.html`, so
russ.frostlinenorge.no/a and /b; noindex, canonical to the front page). All three are also
built as `preview-a.html`, `preview-b.html`, `preview-c.html` for local use (gitignored):

- **a, Lookbook**: the logo, then every garment as a tile; hovering a tile turns the model
  photo into a group wearing it. Then the name ticker and the groups in black and white.
- **b, Kampanje**: a wall of the groups behind the logo, then a panel per garment: a group
  wearing it on one half, the outlined varsity name and the model photo on the other,
  alternating sides and side by side on phones too; then the groups edge to edge.
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

## Changing things

- **Swap a photo under a garment**: edit its `worn` list in `products.json`, run `build.py`.
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
