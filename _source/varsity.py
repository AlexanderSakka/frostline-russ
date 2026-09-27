"""Product names in Varsity, as SVG outlines baked into the page.

Varsity (Brøderbund Software, 1996, from dafont.com) comes with no licence, so the font
file itself is never published: it lives in _source/fonts/ (gitignored, this Mac only)
and the build draws each name from its outlines. The page gets shapes, not a font.

  svg('Zip hoodie', 'vname')   ->  '<svg class="vname" viewBox=...><path d=.../></svg>'

The path is filled with currentColor, so CSS picks the colour: black on the white product
cards, white on the dark product page. The inline stripe inside each letter is a gap in the
glyph, so the background shows through it.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

S = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(S, 'fonts', 'varsity_regular.ttf')
_font = None


def font():
    global _font
    if _font is None:
        if not os.path.exists(FONT):
            raise SystemExit(f'{FONT} is missing: download Varsity from https://www.dafont.com/varsity-2.font '
                             'and unzip varsity_regular.ttf there (it stays out of git)')
        _font = TTFont(FONT)
    return _font


def _kern(f):
    pairs = {}
    if 'kern' in f:
        for t in f['kern'].kernTables:
            pairs.update(getattr(t, 'kernTable', {}))
    return pairs


def svg(text, cls='vname', tracking=20):
    """The text in upper case as one path, its viewBox tight around the ink. tracking is in
    font units (1000 per em) added between letters."""
    f = font()
    cmap, gs, hmtx = f.getBestCmap(), f.getGlyphSet(), f['hmtx']
    kern = _kern(f)
    text = text.upper()
    pen = SVGPathPen(gs)
    bounds = BoundsPen(gs)
    x, prev = 0, None
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            g = cmap[ord(' ')]
        if prev:
            x += kern.get((prev, g), 0)
        # flip y: font units grow upwards, SVG downwards
        gs[g].draw(TransformPen(pen, (1, 0, 0, -1, x, 0)))
        gs[g].draw(TransformPen(bounds, (1, 0, 0, -1, x, 0)))
        x += hmtx[g][0] + (tracking if ch != ' ' else 0)
        prev = g
    x0, y0, x1, y1 = bounds.bounds
    pad = 6
    x0, y0, w, h = x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    return (f'<svg class="{cls}" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" style="--ar:{w / h:.4f}" '
            f'aria-hidden="true" focusable="false"><path fill="currentColor" fill-rule="nonzero" '
            f'd="{pen.getCommands()}"/></svg>')
