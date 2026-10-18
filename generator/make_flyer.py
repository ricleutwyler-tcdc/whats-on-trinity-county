#!/usr/bin/env python3
"""
Trinity County "What's On" — printable one-page flyer for bulletin boards.

Reads the finished, curated index.html (run it after curation and weather) and writes
flyer.html: one letter-size page listing the next seven days, with a QR code to the site.
It is published next to index.html, so anyone can print it from
events.trinitycommunitydev.org/flyer.html.

Usage: python3 make_flyer.py <index.html> <flyer.html> [YYYY-MM-DD first day]
The first day defaults to today. Uses the event text exactly as curated; it adds nothing.
"""
import sys, re, json, html, datetime, os

SITE = "https://events.trinitycommunitydev.org"
J = "https://www.trinityjournal.com/calendar/"


def js_to_json(src):
    """The EVENTS block is JS object literals: bare keys, double-quoted strings, and J.
    Quote the keys and resolve J, leaving everything inside strings alone."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':                                   # copy a string verbatim
            j = i + 1
            while src[j] != '"':
                j += 2 if src[j] == '\\' else 1
            out.append(src[i:j + 1]); i = j + 1
        elif c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'):
                j += 1
            word = src[i:j]
            k = j
            while k < n and src[k] == ' ':
                k += 1
            if k < n and src[k] == ':':
                out.append(json.dumps(word))
            elif word == 'J':
                out.append(json.dumps(J))
            else:
                out.append(word)                       # true / false / null
            i = j
        elif src.startswith('//', i):                  # comment line
            i = src.index('\n', i)
        else:
            out.append(c); i += 1
    text = ''.join(out)
    return re.sub(r',\s*([\]}])', r'\1', text)         # no trailing commas in JSON


def load_events(index_html):
    m = re.search(r'const EVENTS = (\[.*?\n\]);', index_html, re.S)
    if not m:
        sys.exit("no EVENTS block in the page")
    return json.loads(js_to_json(m.group(1)))


TIME = re.compile(r'(\d{1,2})(?::(\d{2}))?(?:–(\d{1,2})(?::(\d{2}))?)? (AM|PM)$')


def start_minutes(e):
    m = TIME.search(e['dayLabel'])
    if not m:
        return -1                                      # all-day sorts first
    h = int(m.group(1)) % 12 + (12 if m.group(5) == 'PM' else 0)
    if m.group(3):
        eh = int(m.group(3)) % 12 + (12 if m.group(5) == 'PM' else 0)
        if h > eh:
            h -= 12                                    # "11–2 PM" starts in the morning
    return h * 60 + int(m.group(2) or 0)


def time_text(e):
    parts = e['dayLabel'].split(' · ')
    return parts[2] if len(parts) > 2 else (parts[1] if parts[0].startswith(('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')) and '–' in parts[0] else 'All day')


def plain(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def main():
    page = open(sys.argv[1], encoding='utf-8').read()
    out = sys.argv[2]
    first = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime.date.today()
    last = first + datetime.timedelta(days=6)
    events = load_events(page)
    fills = dict(re.findall(r"'([^']+)'\s*:\s*'(#[0-9A-Fa-f]{6})'",
                            re.search(r'const CAT_FILL = \{(.*?)\};', page, re.S).group(1)))
    fill = lambda e: fills.get(e['cat'].split(' · ')[0], '#14564D')

    dated = [e for e in events if not e.get('weekly')
             and first <= datetime.date.fromisoformat(e['date']) <= last]
    dated.sort(key=lambda e: (e['date'], start_minutes(e)))
    weekly = [e for e in events if e.get('weekly')]

    days = {}
    for e in dated:
        days.setdefault(e['date'], []).append(e)

    blocks = []
    for d, evs in days.items():
        dt = datetime.date.fromisoformat(d)
        rows = ''.join(
            f'<li style="--cc:{fill(e)}"><span class="t">{html.escape(time_text(e))}</span>'
            f'<span class="n">{html.escape(plain(e["title"]))}</span>'
            f'<span class="w">{html.escape(plain(e["where"]))}</span></li>' for e in evs)
        blocks.append(f'<section class="day"><h2>{dt.strftime("%A")} <span>{dt.strftime("%b")} {dt.day}</span></h2><ul>{rows}</ul></section>')

    weekly_line = ' · '.join(
        f'{html.escape(plain(e["title"]))} ({html.escape(e["dayLabel"].replace("Weekly · ", ""))})' for e in weekly)
    span = f'{first.strftime("%b")} {first.day} – {last.strftime("%b")} {last.day}, {last.year}'
    size = 'tight' if len(dated) > 22 else ('roomy' if len(dated) < 12 else '')
    qr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flyer-qr.svg'), encoding='utf-8').read()
    qr = re.sub(r'width="\d+" height="\d+"', 'viewBox="0 0 29 29" width="100%" height="100%"', qr, count=1)

    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>What's On in Trinity County · {span}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  @page{{size:letter;margin:0.45in}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:#E8E1D3;font-family:'DM Sans',system-ui,sans-serif;color:#2E2A22}}
  .sheet{{width:7.6in;min-height:10.1in;margin:24px auto;background:#fff;padding:0 0 .2in;display:flex;flex-direction:column;
         box-shadow:0 2px 14px rgba(0,0,0,.15)}}
  header{{background:#14564D;color:#fff;padding:.22in .3in .2in}}
  .kick{{font-size:10.5pt;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#E7A94A;margin:0}}
  h1{{font-family:Georgia,'Times New Roman',serif;font-size:27pt;margin:.03in 0 .02in;line-height:1.05}}
  .span{{font-size:13pt;margin:0}}
  main{{columns:2;column-gap:.32in;padding:.18in .3in 0;flex:1}}
  .day{{break-inside:avoid;margin:0 0 .13in}}
  .day h2{{font-family:Georgia,'Times New Roman',serif;font-size:14pt;color:#14564D;margin:0 0 .04in;padding-bottom:.03in;border-bottom:1.5px solid #E8E1D3}}
  .day h2 span{{font-family:'DM Sans',system-ui,sans-serif;font-size:10.5pt;color:#6F6A5E;font-weight:600}}
  ul{{list-style:none;margin:0;padding:0}}
  li{{border-left:4px solid var(--cc);padding:.02in 0 .02in .09in;margin:0 0 .06in;display:grid;grid-template-columns:auto 1fr;column-gap:.08in}}
  .t{{font-size:9.5pt;font-weight:700;white-space:nowrap;padding-top:1px}}
  .n{{font-family:Georgia,'Times New Roman',serif;font-size:11pt;font-weight:700;line-height:1.2}}
  .w{{grid-column:2;font-size:9pt;color:#6F6A5E;line-height:1.25}}
  .tight .n{{font-size:10pt}} .tight .w{{font-size:8.5pt}} .tight li{{margin-bottom:.04in}} .tight .day{{margin-bottom:.09in}}
  .roomy .n{{font-size:12.5pt}} .roomy .t{{font-size:10.5pt}} .roomy .w{{font-size:10pt}} .roomy li{{margin-bottom:.1in}}
  .weekly{{margin:.06in .3in 0;padding:.08in .12in;background:#FAF6EF;border-radius:6px;font-size:9pt;line-height:1.35}}
  .weekly b{{color:#14564D}}
  footer{{display:flex;align-items:center;gap:.2in;margin:.14in .3in 0;padding-top:.12in;border-top:1.5px solid #E8E1D3}}
  .qr{{width:1in;height:1in;flex:none}}
  .ft{{font-size:10.5pt;line-height:1.4}}
  .ft .url{{font-family:Georgia,'Times New Roman',serif;font-size:15pt;font-weight:700;color:#14564D;display:block}}
  .ft small{{display:block;color:#6F6A5E;font-size:8.5pt;margin-top:.04in}}
  .signoff{{font-family:Georgia,'Times New Roman',serif;font-style:italic;color:#14564D}}
  .print{{display:block;margin:16px auto 0;font:inherit;font-weight:700;background:#14564D;color:#fff;border:0;border-radius:10px;padding:10px 18px;cursor:pointer}}
  @media print{{body{{background:#fff}} .sheet{{margin:0;box-shadow:none;width:auto;min-height:0}} .print{{display:none}}
               header,li,.weekly{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head>
<body>
<button class="print" onclick="window.print()">Print this flyer</button>
<div class="sheet {size}">
  <header>
    <p class="kick">This week</p>
    <h1>What's On in Trinity County</h1>
    <p class="span">{span}</p>
  </header>
  <main>
    {"".join(blocks) or '<p>No dated events this week. See the website for what is coming up.</p>'}
  </main>
  {f'<div class="weekly"><b>Every week:</b> {weekly_line}</div>' if weekly_line else ''}
  <footer>
    <div class="qr">{qr}</div>
    <div class="ft">Times, places, maps and more events, updated every week:
      <span class="url">events.trinitycommunitydev.org</span>
      Free to list your event. <span class="signoff">This is Trinity County.</span>
      <small>A TCDC and Trinity Journal collaboration · events from The Trinity Journal's weekly calendar</small>
    </div>
  </footer>
</div>
</body></html>
'''
    open(out, 'w', encoding='utf-8').write(doc)
    print(f"flyer: {span} · {len(dated)} dated events on {len(days)} days · {len(weekly)} weekly")


if __name__ == '__main__':
    main()
