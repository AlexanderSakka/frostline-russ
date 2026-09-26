# russ.frostlinenorge.no

Frostline's showcase for russegrupper: the four garments first (zip hoodie, hoodie,
crewneck, bukse), then the groups that wear them. There is no shop and no email on the
page on purpose; the only way in is a DM to @frostlineno on Instagram.

Hosted on GitHub Pages from `main`; `CNAME` pins the custom domain. `index.html` is
generated, never edit it by hand.

## Files

- `index.html`: the page, written by `_source/build.py`.
- `style.css` + `app.js`: shared by every style. `v-a.css`, `v-b.css`, `v-c.css`: the three styles.
- `img/<post>-<slide>-{s,m,l}.webp`: Instagram photos at 480, 900 and 1440 px.
- `img/p/`: the garment studio shots (`<garment>-<graa|navy>-<front|back>-<600|1000>.webp`,
  `<garment>-life-*.webp`) and the transparent line-up used in style a.
- `assets/`: logos, `og.jpg` (link preview), `mosaic.jpg` (style b's hero).
- `_source/`: the data and the scripts (below). `_source/raw/` holds the Instagram
  originals and is gitignored.

## The three styles

`_source/site.json` says which one is live. All three are built every time as
`preview-a.html`, `preview-b.html`, `preview-c.html` (gitignored, noindex) so they can be
compared locally:

- **a, Lookbook**: the logo over the four garments, a studio per garment (side, colour, cut,
  on a model) with a row of photos from the groups, then the groups in black and white.
- **b, Kampanje**: a wall of the groups behind the logo, one full photo panel per garment
  with its name in outlined varsity type, then the groups edge to edge.
- **c, Indeks**: black and closed, the garments as an index you open one by one, the groups
  as a name list whose photo follows the pointer.

```
python3 _source/build.py            # rebuild index.html and the previews
python3 _source/build.py --live b   # switch the live style
python3 -m http.server 8765         # then open http://localhost:8765/preview-a.html
```

## Data

- `_source/products.json`: the garments in page order, their print spots, and which
  Instagram photos show each one (`worn`, best first).
- `_source/groups.json`: one row per group card (name, handle, cover, extra posts in `also`).
- `_source/posts.json`: captions and image list per Instagram post.

## Changing things

- **Swap a photo under a garment**: edit its `worn` list in `products.json`, run `build.py`.
- **Add a group**: put the post's images in `_source/raw/` as `<post>-<slide>.jpg`, add a
  `posts.json` entry and a `groups.json` row, run `python3 _source/make_webp.py`, then
  `build.py`.
- **New garment mockups**: they come from the skole repo (`~/skole/assets` and
  `~/skole/mockups-ai`), the same pictures frostlinenorge.no sells from. Run
  `python3 _source/make_product_images.py`, then `build.py`.

Commit and push; Pages redeploys in about a minute.
