"""Render the share card (og-image.png) from the site's own hero.

Same approach as the Community Resources Hub's build/make_og_image.py:
nothing is drawn here that is not already on the page. The hero art, eyebrow,
headline and subtitle are the live ones; the buttons and the date/count row are
hidden and the site address is added under the subtitle. Rerun after a hero
design change; the weekly build does not need it (it is evergreen).

Run from the repo root:  python3 generator/make_og_image.py
"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
OUT = ROOT / "og-image.png"
ADDRESS = "events.trinitycommunitydev.org"

CSS = f"""
header.nhero{{height:628px !important;min-height:628px !important}}
header.nhero .nh-actions,header.nhero .meta-row{{display:none !important}}
header.nhero .nh-content{{padding:0 84px 64px !important;max-width:none !important}}
header.nhero .nh-eyebrow{{font-size:15px !important;letter-spacing:.18em !important}}
header.nhero h1{{font-size:72px !important;line-height:1.02 !important}}
header.nhero .nh-sub{{font-size:23px !important;max-width:760px !important;margin:0 !important}}
header.nhero .nh-content::after{{content:"{ADDRESS}";display:block;margin-top:18px;
  font:700 20px/1 'DM Sans',system-ui,sans-serif;color:#E7A94A;letter-spacing:.01em}}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=1)
    pg.goto(PAGE.as_uri(), wait_until="networkidle")
    pg.add_style_tag(content=CSS)
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(500)
    pg.locator("header.nhero").screenshot(path=str(OUT))
    b.close()
print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
