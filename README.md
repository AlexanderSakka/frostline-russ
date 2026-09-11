# russ.frostlinenorge.no

Static showcase of the russegrupper Frostline has delivered gruppeklær to.
Photos and group names come from the @frostlineno Instagram account.

- `index.html`, `style.css`, `app.js`: the page (one scrollable collage, lightbox, one contact button).
- `img/<post>-<slide>-m.webp` (max 900 px, grid) and `-l.webp` (max 1440 px, lightbox).
- Hosted on GitHub Pages; `CNAME` pins the custom domain.

To add a group: drop the images in `img/` with the same naming, then add a card in `index.html`
(copy an existing `<article class="card">`) and an entry in the inline `#data` JSON for the lightbox.
