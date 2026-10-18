#!/usr/bin/env python3
"""
Check the event-card category colours against the Brand 2.0 §2a rules.

Reads the CAT_FILL map out of the page (template.html or the built index.html) and
fails if:
  - white text on any fill is under 4.5:1 (the card title and date sit in white on it),
  - two different fills are closer than ΔE 20 in CIELAB (they'd read as one colour),
  - more than nine different fills are in use (the §2a ceiling).

Usage:
    python3 check-colours.py index.html

Exit code 1 if anything fails, so it can gate a build.
"""
import re, sys, itertools

MIN_CONTRAST = 4.5
MIN_DELTA_E = 20
MAX_FILLS = 9


def channel(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(hexc):
    h = hexc.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def luminance(hexc):
    r, g, b = (channel(c) for c in rgb(hexc))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_white(hexc):
    return 1.05 / (luminance(hexc) + 0.05)


def lab(hexc):
    r, g, b = (channel(c) for c in rgb(hexc))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.0
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    return sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))) ** 0.5


def main(path):
    src = open(path, encoding='utf-8').read()
    m = re.search(r'const CAT_FILL = \{(.*?)\};', src, re.S)
    if not m:
        print(f'{path}: no CAT_FILL map found')
        return 1
    pairs = re.findall(r"'([^']+)'\s*:\s*'(#[0-9A-Fa-f]{6})'", m.group(1))
    fills = {}
    for cat, col in pairs:
        fills.setdefault(col.upper(), []).append(cat)
    fails = 0
    for col, cats in fills.items():
        cr = contrast_white(col)
        ok = cr >= MIN_CONTRAST
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {col}  white {cr:5.2f}:1  {', '.join(cats)}")
    for a, b in itertools.combinations(fills, 2):
        d = delta_e(a, b)
        if d < MIN_DELTA_E:
            fails += 1
            print(f'FAIL {a} vs {b}  ΔE {d:.1f} (under {MIN_DELTA_E})')
    closest = min(itertools.combinations(fills, 2), key=lambda p: delta_e(*p))
    print(f'closest pair {closest[0]} / {closest[1]}: ΔE {delta_e(*closest):.1f}')
    if len(fills) > MAX_FILLS:
        fails += 1
        print(f'FAIL {len(fills)} fills in use (ceiling {MAX_FILLS})')
    print('clean' if not fails else f'{fails} problem(s)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'index.html'))
