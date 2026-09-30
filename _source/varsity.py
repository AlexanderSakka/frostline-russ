"""Product names in Varsity, as SVG outlines baked into the page.

Varsity (Brøderbund Software, 1996, from dafont.com) comes with no licence, so the font
file itself is never published: it lives in _source/fonts/ (gitignored, this Mac only)
and the build draws each name from its outlines. The page gets shapes, not a font.

  svg('Zip hoodie', 'vname')   ->  '<svg class="vname" viewBox=...><path d=.../></svg>'

The path is filled with currentColor, so CSS picks the colour: black on the white product
cards, white on the dark product page. The inline stripe inside each letter is a gap in the
glyph, so the background shows through it.

The font's own Ø is not a Varsity letter: a solid block with a slash stuck on, none of the
outline the other letters have, and lower and shorter than its O (it made STØRRELSER on the
size guide look broken). So Ø is drawn here from the font's O instead (oslash below); needs
shapely (pip3 install --user shapely). Æ is as bad in the font and is not rebuilt; no name
uses it.
"""
import math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen

S = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(S, 'fonts', 'varsity_regular.ttf')
_font = None
_oslash = None


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


def oslash(angle=60, thick=88):
    """Ø as the font would draw it: its O with a bar through the counter, merged into the
    letter's body, and the outline redrawn round the whole the way the font outlines every
    letter. The O is six outlines, outside in: ring, gap, body, counter, gap, ring; the gap
    is 21 units wide and the ring reaches 39 from the body. The bar crosses the O's centre
    at `angle` degrees, `thick` units across, and stops at the O's edge, so the letter keeps
    the O's shape and the slash splits the counter in two, each with its inner ring.
    Returns the contours in font units (y up), outer ones clockwise as in the font."""
    global _oslash
    if _oslash is None:
        try:
            from shapely.geometry import Polygon, MultiPolygon
            from shapely.geometry.polygon import orient
            from shapely.ops import unary_union
        except ImportError:
            raise SystemExit('varsity.py draws Ø with shapely: pip3 install --user --break-system-packages shapely')
        rec = RecordingPen()
        font().getGlyphSet()['O'].draw(rec)
        contours = []
        for op, args in rec.value:
            if op == 'moveTo':
                contours.append([args[0]])
            elif op == 'lineTo':
                contours[-1].append(args[0])
        body, edge = Polygon(contours[2], [contours[3]]), Polygon(contours[2])
        (x0, y0, x1, y1), a = edge.bounds, math.radians(angle)
        cx, cy, ux, uy, h = (x0 + x1) / 2, (y0 + y1) / 2, math.cos(a), math.sin(a), thick / 2
        bar = Polygon([(cx - ux * 900 - uy * h, cy - uy * 900 + ux * h), (cx + ux * 900 - uy * h, cy + uy * 900 + ux * h),
                       (cx + ux * 900 + uy * h, cy + uy * 900 - ux * h), (cx - ux * 900 + uy * h, cy - uy * 900 - ux * h)])
        letter = unary_union([body, bar]).intersection(edge)
        # close the hairline slivers where the bar meets the O's edge, or the outline spikes there
        letter = letter.buffer(0.5, join_style='mitre').buffer(-0.5, join_style='mitre')
        grow = lambda d: letter.buffer(d, join_style='mitre', mitre_limit=2)
        shape = unary_union([letter, grow(39).difference(grow(21))])
        _oslash = []
        for p in (shape.geoms if isinstance(shape, MultiPolygon) else [shape]):
            p = orient(p, sign=-1.0)
            _oslash += [[(round(x, 1), round(y, 1)) for x, y in r.coords[:-1]] for r in [p.exterior, *p.interiors]]
    return _oslash


def _draw_contours(contours, pens, x):
    for pen in pens:
        t = TransformPen(pen, (1, 0, 0, -1, x, 0))
        for c in contours:
            t.moveTo(c[0])
            for pt in c[1:]:
                t.lineTo(pt)
            t.closePath()


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
        # Ø is drawn from O, so it spaces and kerns as O does
        g = 'O' if ch == 'Ø' else cmap.get(ord(ch))
        if g is None:
            g = cmap[ord(' ')]
        if prev:
            x += kern.get((prev, g), 0)
        # flip y: font units grow upwards, SVG downwards
        if ch == 'Ø':
            _draw_contours(oslash(), (pen, bounds), x)
        else:
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
