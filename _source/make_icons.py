"""The favicon and home-screen icons: the varsity F of the wordmark, white on the site's black.

  python3 _source/make_icons.py

Search results show the favicon next to the site name, so it is the logo's own F rather
than a plain letter. Writes assets/favicon.png (96 px), assets/apple-touch-icon.png (180 px)
and favicon.ico (16, 32, 48 px) at the root, where browsers and crawlers look without asking.
"""
import os
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(S)
BG = (9, 9, 11)

word = Image.open(f'{SITE}/assets/frostline-logo-white.png')
alpha = word.getchannel('A')
x = 0
while any(alpha.getpixel((x, y)) > 40 for y in range(word.height)):  # the F ends at the first empty column
    x += 1
F = word.crop((0, 0, x, word.height))


def icon(n, pad):
    c = Image.new('RGBA', (n, n), BG + (255,))
    h = round(n * (1 - 2 * pad))
    g = F.resize((max(1, round(F.width * h / F.height)), h), Image.LANCZOS)
    c.alpha_composite(g, ((n - g.width) // 2, (n - g.height) // 2))
    return c.convert('RGB')


icon(96, .16).save(f'{SITE}/assets/favicon.png', optimize=True)
icon(180, .16).save(f'{SITE}/assets/apple-touch-icon.png', optimize=True)
icon(48, .12).save(f'{SITE}/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
print(f'F is {x} px wide; wrote favicon.png, apple-touch-icon.png, favicon.ico')
