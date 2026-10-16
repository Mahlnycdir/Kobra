"""Erzeugt die App-Icons (Kobra-Zeichen) in mehreren Groessen."""
from PIL import Image, ImageDraw
import math, os

OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')

def bezier(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts

def draw(size, maskable=False):
    S = 4 * size
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = 0 if maskable else int(S * 0.225)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill=(22, 25, 31, 255))
    sc = 0.78 if maskable else 1.0
    def P(x, y):
        return (S/2 + (x - 0.5) * S * sc, S/2 + (y - 0.5) * S * sc)
    # Schlangenkoerper als S-Kurve
    body = bezier(P(0.30, 0.82), P(0.95, 0.80), P(0.10, 0.45), P(0.62, 0.30), 1200)
    w = int(S * 0.11 * sc)
    yellow = (242, 201, 76, 255)
    n = len(body)
    for i, p in enumerate(body):
        rr = w / 2 * (0.75 + 0.45 * i / n)
        d.ellipse([p[0]-rr, p[1]-rr, p[0]+rr, p[1]+rr], fill=yellow)
    # Kopf (Kobra-Haube)
    hx, hy = P(0.64, 0.25)
    hw, hh = S*0.15*sc, S*0.12*sc
    d.ellipse([hx-hw, hy-hh, hx+hw, hy+hh], fill=yellow)
    # Augen
    er = S*0.022*sc
    for ex in (-0.055, 0.055):
        cx, cy = hx + ex*S*sc, hy - 0.01*S*sc
        d.ellipse([cx-er, cy-er, cx+er, cy+er], fill=(22, 25, 31, 255))
    # Prompt-Zeichen links unten
    blue = (106, 167, 255, 255)
    lw = int(S*0.045*sc)
    a, b, c = P(0.17, 0.30), P(0.29, 0.385), P(0.17, 0.47)
    d.line([a, b], fill=blue, width=lw)
    d.line([b, c], fill=blue, width=lw)
    for p in (a, b, c):
        d.ellipse([p[0]-lw/2, p[1]-lw/2, p[0]+lw/2, p[1]+lw/2], fill=blue)
    return img.resize((size, size), Image.LANCZOS)

os.makedirs(OUT, exist_ok=True)
draw(192).save(os.path.join(OUT, 'icon-192.png'))
draw(512).save(os.path.join(OUT, 'icon-512.png'))
draw(512, maskable=True).save(os.path.join(OUT, 'icon-maskable-512.png'))
ap = draw(180, maskable=True).convert('RGB')
ap.save(os.path.join(OUT, 'apple-touch-icon.png'))
print('ok')
