#!/usr/bin/env python3
"""
inject_weather.py — add live forecasts to a generated What's-On index.html.

Why this exists: generate_site.py runs in a sandbox with no outbound network,
so it cannot fetch weather and emits wx:null for every event. The weekly task's
agent CAN reach the National Weather Service via WebFetch. So the agent fetches
a 7-day forecast per town, writes it to weather.json, and runs this script to
fill each event's wx.

Usage:  python3 inject_weather.py <index.html> <weather.json> [out.html]
        (out.html defaults to overwriting index.html)

weather.json format:
{
  "generated": "2026-08-13",          # the run date (forecast base), YYYY-MM-DD
  "reference": "Weaverville",         # fallback town for unmatched locations
  "byTown": {
    "Weaverville": { "2026-08-14": {"hi":86,"lo":52,"txt":"Sunny"}, ... },
    "Hayfork":     { "2026-08-15": {"hi":95,"lo":58,"txt":"Sunny"}, ... },
    ...
  }
}

Rules:
- Dated event: use its own date. Weekly event: use the next occurrence of the
  weekday named in its dayLabel, on/after the generated date.
- Match the event's town from its map/where text; unmatched -> reference town,
  and " · approx." is appended to the conditions text.
- hot = high >= 98 (drives the red "heat" badge, matching the site's rule).
- If no forecast exists for that town+date (e.g. beyond the 7-day window or a
  past event), wx is left null -> the site shows "Forecast closer to the date".
"""
import sys, re, json, datetime

WD = {'sunday':6,'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5}

# Town-name aliases used to match an event's location text to a forecast town.
# Outlying towns (climate differs from the Weaverville reference) are flagged so
# a reference-based fallback is labelled "approx.".
TOWN_ALIASES = {
    'Weaverville':   ['weaverville'],
    'Hayfork':       ['hayfork'],
    'Lewiston':      ['lewiston'],
    'Trinity Center':['trinity center','coffee creek','koa'],
    'Junction City': ['junction city'],
    'Hyampom':       ['hyampom'],
    'Big Bar':       ['big bar','del loma'],
    'Ruth':          ['ruth','mad river','ruth lake'],
}
OUTLYING = {'Hayfork','Trinity Center','Junction City','Hyampom','Big Bar','Ruth'}


def town_for(blob):
    b = blob.lower()
    for town, keys in TOWN_ALIASES.items():
        if any(k in b for k in keys):
            return town
    return None


def event_objects(arr):
    """Yield (start,end) spans of top-level { } objects within the array text."""
    d = 0; start = None
    for i, c in enumerate(arr):
        if c == '{':
            if d == 0: start = i
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                yield (start, i + 1)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    html_path, wx_path = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else html_path

    t = open(html_path, encoding='utf-8').read()
    wx = json.load(open(wx_path, encoding='utf-8'))
    base = datetime.date.fromisoformat(wx['generated'])
    ref_town = wx.get('reference', 'Weaverville')
    by_town = wx['byTown']

    def lookup(town, dstr):
        """Return (hi,lo,txt,approx) or None."""
        if town and town in by_town and dstr in by_town[town]:
            f = by_town[town][dstr]; return (f['hi'], f['lo'], f['txt'], False)
        if ref_town in by_town and dstr in by_town[ref_town]:
            f = by_town[ref_town][dstr]
            # Only flag "approx." for a genuinely outlying town borrowing the
            # reference forecast. An unmatched venue (town is None) or a
            # Weaverville-area one is treated as exact — no approx tag.
            return (f['hi'], f['lo'], f['txt'], town in OUTLYING)
        return None

    i = t.index('EVENTS'); lb = t.index('[', i)
    d = 0; j = lb
    while j < len(t):
        if t[j] == '[': d += 1
        elif t[j] == ']':
            d -= 1
            if d == 0: break
        j += 1
    arr = t[lb:j + 1]; head, tail = t[:lb], t[j + 1:]

    new = arr; filled = 0; total = 0
    for (s, e) in reversed(list(event_objects(arr))):
        obj = arr[s:e]
        dm = re.search(r'date:"(\d{4}-\d{2}-\d{2})"', obj)
        if not dm:
            continue
        total += 1
        weekly = 'weekly:true' in obj
        blob = ' '.join([
            (re.search(r'map:"([^"]*)"', obj) or [None, ''])[1],
            (re.search(r'where:"([^"]*)"', obj) or [None, ''])[1],
        ])
        town = town_for(blob)

        target = None; extra = ''
        if weekly:
            dl = (re.search(r'dayLabel:"([^"]*)"', obj) or [None, ''])[1].lower()
            wd = next((v for k, v in WD.items() if k in dl), None)  # schedule label only
            if wd is not None:
                target = (base + datetime.timedelta(days=(wd - base.weekday()) % 7)).isoformat()
            if 'golf' in obj.lower():
                extra = ' · cooler at tee time'
        else:
            target = dm.group(1)

        newwx = 'wx:null'
        if target:
            got = lookup(town, target)
            if got:
                hi, lo, txt, approx = got
                txt = txt + extra + (' · approx.' if approx else '')
                newwx = 'wx:{hi:%d,lo:%d,txt:"%s",hot:%s}' % (hi, lo, txt, 'true' if hi >= 98 else 'false')
                filled += 1
        obj2 = re.sub(r'wx:null|wx:\{[^}]*\}', newwx, obj, count=1)
        new = new[:s] + obj2 + new[e:]

    out = head + new + tail
    # refresh the "Updated <Mon D, YYYY>" stamp to the run date
    stamp = base.strftime('%b %-d, %Y')
    out = re.sub(r'Updated [A-Z][a-z]+ \d{1,2}, \d{4}', 'Updated ' + stamp, out)
    open(out_path, 'w', encoding='utf-8').write(out)
    print('inject_weather: %d/%d events given a live forecast (rest -> "closer to the date")' % (filled, total))


if __name__ == '__main__':
    main()
