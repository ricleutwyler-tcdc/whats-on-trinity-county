#!/usr/bin/env python3
"""
Trinity County "What's On" — public events.json for other sites (the Revitalization Hub).

Reads the finished, curated index.html and writes events.json at the repo root: every
dated event from the given day onward (weekly fixtures skipped), with only what the page
already shows. Run it whenever index.html changes, next to make_flyer.py.

Usage: python3 export_events.py <index.html> <events.json> [YYYY-MM-DD from]
The day defaults to today. Sites reading the file should still hide events whose date has
passed, since the file is only rewritten when the page is.
"""
import sys, re, json, datetime, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_flyer import load_events, plain   # same EVENTS parser the flyer uses

SITE = "https://events.trinitycommunitydev.org/"

# The towns the "Add your event" form offers (submit.html), most specific first so that
# "Coffee Creek Country Store, Trinity Center" counts as Coffee Creek.
TOWNS = [
    ("Coffee Creek", ["coffee creek"]),
    ("Ruth / Mad River", ["ruth", "mad river"]),
    ("Burnt Ranch", ["burnt ranch"]),
    ("Big Bar", ["big bar"]),
    ("Junction City", ["junction city"]),
    ("Douglas City", ["douglas city"]),
    ("Trinity Center", ["trinity center"]),
    ("Hyampom", ["hyampom"]),
    ("Salyer", ["salyer"]),
    ("Zenia", ["zenia"]),
    ("Hayfork", ["hayfork"]),
    ("Lewiston", ["lewiston"]),
    ("Weaverville", ["weaverville"]),
]


# Regular venues whose address on the card often leaves the town out.
VENUES = [
    ("trinity county brewing", "Weaverville"),
    ("trinity alps performing arts", "Weaverville"),
    ("highland art center", "Weaverville"),
    ("tangle blue", "Weaverville"),
    ("holiday market", "Weaverville"),
    ("jc community", "Junction City"),
]


def town_of(e):
    """Town from the card's place, then its map address, then a known venue. 'Other' if none names one."""
    texts = [plain(e.get("where", "")).lower(), plain(e.get("map", "")).lower()]
    for t in texts:
        for name, keys in TOWNS:
            if any(re.search(r"\b" + re.escape(k) + r"\b", t) for k in keys):
                return name
    for venue, name in VENUES:
        if any(venue in t for t in texts):
            return name
    return "Other"


def ev_id(e):
    """Same id the page gives each card (evId in template.html), so links open that card."""
    slug = re.sub(r"[^a-z0-9]+", "-", plain(e["title"]).lower()).strip("-")[:40]
    return "ev-" + e["date"] + "-" + slug


def main():
    page = open(sys.argv[1], encoding="utf-8").read()
    out = sys.argv[2]
    start = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().isoformat()
    events = [e for e in load_events(page) if not e.get("weekly") and e["date"] >= start]
    events.sort(key=lambda e: e["date"])
    data = {
        "as_of": start,
        "source": SITE,
        "events": [{
            "date": e["date"],
            "day_label": e["dayLabel"],
            "title": plain(e["title"]),
            "where": plain(e["where"]),
            "town": town_of(e),
            "category": e["cat"],
            "url": SITE + "#" + ev_id(e),
        } for e in events],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"events.json: {len(events)} events from {start}")
    for e in data["events"]:
        print(f"  {e['date']}  {e['town']:<16} {e['title'][:44]:<44} ← {e['where'][:60]}")


if __name__ == "__main__":
    main()
