# What's On in Trinity County — Weekly Build Runbook

This is the exact procedure the weekly scheduled task follows to rebuild the site from
Wayne Agner's Trinity Journal calendar. Follow it top to bottom. It is written to be run
by a fresh session with no memory of prior weeks.

## Non-negotiables (read first)

1. **Never publish to the live site.** Do NOT `git push`, do NOT commit to `main`, do NOT
   use any GitHub token to write to the remote. Your job ends at putting the finished
   `index.html` in front of Ric. He reviews the diff in GitHub Desktop and pushes. That
   review is the safety gate — keep it.
2. **Verify in the rendered page, not just the source.** Render the built page and read it
   before handing it over. Checkers and greps read source; they cannot see a defect that
   only shows once the page renders.
3. **Editorial descriptions are your job, not the generator's.** The generator writes safe
   placeholder text for events it doesn't recognize. You rewrite every one of those in
   Ric's voice (see Voice, below).
4. **When something is genuinely uncertain, leave it accurate and flag it to Ric** rather
   than inventing detail.

## Inputs and where they live

- **The calendar**: emailed by Wayne Agner, `publisher@trinityjournal.com`, as a `.txt`
  attachment, Thursday evening through noon Friday each week.
- **The repo**: `https://github.com/ricleutwyler-tcdc/whats-on-trinity-county` (public;
  the cloud can *read/clone* it but CANNOT push — a proxy blocks writes).
- **The build tools** (in the repo under `generator/`): `generate_site.py`,
  `inject_weather.py`, `template.html`, `curate_overrides.py` (example), and
  `checks/check-claims.py`, `checks/check-voice.py`.
- **The rubric** (categorization + registry source of truth): Google Drive doc
  `1msg7NQsP-vPVwy1YKmfpDr-bgNPVSPjKqoqUolvhDqE`. The same rules are mirrored in the
  `REGISTRY` inside `generate_site.py`.
- **Ric's delivery rules**: the `delivering-work-to-ric` skill (voice, claims, handover).

## Steps

### 1. Get this week's calendar
Gmail search — **no subject filter** (Wayne's subject line varies):
```
from:publisher@trinityjournal.com has:attachment newer_than:9d
```
Open the newest match, get the message RAW (`get_message`, messageFormat RAW), decode the
base64url MIME, and save the `.txt` attachment. Confirm the header line reads
`TRINITY COUNTY CALENDAR OF EVENTS M-DD-YY`. If no new calendar has arrived since the last
run, stop and tell Ric — do not rebuild from an old one.

### 2. Get the build tools
Clone the repo (read is fine) into your workspace. Use `generator/generate_site.py`,
`generator/template.html`, `generator/inject_weather.py`, and the two checkers under
`generator/checks/`.

### 3. Generate
```
python3 generate_site.py <calendar.txt> template.html index.html <YYYY-MM-DD today>
```
Anchor to **today's date** so the rolling ~2-week window is correct. Read the generator's
stdout: it prints every in-window event with a STATUS tag:
- `locked`  — registry set both category and description. Trust it.
- `cat-only`— registry set the category; **you write the description.**
- `NEW`     — no registry match; **verify the category against the rubric AND write the
  description.** Categories to double-check by hand: anything with "band"/"music" in the
  text that is really a car show, market, or fair; members-only or venue-specific events.

### 4. Curate (the real work)
Apply corrections with a keyed override post-processor — see `curate_overrides.py` for the
exact pattern (match each event object by a unique title substring; rewrite `desc`, `cat`,
`for`, `where`, `map`, `title`, `feat` as needed). Sweep these defect classes every week:

- **Echoed / placeholder descriptions** on `NEW` and `cat-only` events — rewrite all of
  them in Ric's voice. One or two warm, concrete sentences. No echo of the raw line.
- **Truncated `where` fields** — the extractor sometimes stops at "9 a" or "260 S" or
  runs a whole sentence into the venue. Give each a clean venue + town.
- **Run-on or mid-quote titles** — trim to the event's real name (e.g. a concert titled
  with the whole promo sentence → `Performer: "Show"`).
- **Category sanity** — a fly-in / show 'n' shine is **Cars**, not Live Music; a
  members-only PAC event is not the Coffee Creek karaoke; a fundraiser banquet is
  **Community**. When in doubt, the rubric doc wins; if you make a new call, note it for
  Ric so it can be folded into the rubric.
- **Audience** — members-only → locals only; a countywide festival → visitor/local/family.

### 5. Weather
The cloud sandbox blocks weather APIs. The ONLY working channel is `WebFetch` against the
National Weather Service point forecast for Weaverville:
```
https://forecast.weather.gov/MapClick.php?lat=40.7307&lon=-122.9422
```
(This URL is included in the scheduled task's prompt so WebFetch's provenance check passes
— if a fetch is refused for provenance, paste the URL into your own notes/output first.)
Pull the multi-day forecast, then write `weather.json`:
```json
{"generated":"<today YYYY-MM-DD>","reference":"Weaverville",
 "byTown":{"Weaverville":{"YYYY-MM-DD":{"hi":88,"lo":49,"txt":"Sunny"}, ...}}}
```
Keep `txt` short (card-sized): "Sunny", "Mostly sunny", "Patchy AM fog", "Chance showers".
Then:
```
python3 inject_weather.py index.html weather.json
```
Only the next ~7 days get filled; everything beyond keeps "Forecast closer to the date."
Outlying-town events (Trinity Center, Hayfork, Hyampom, Ruth, Junction City) borrowing the
Weaverville forecast are auto-tagged "· approx." — that's correct, leave it.

### 6. Checkers
```
python3 checks/check-claims.py index.html
python3 checks/check-voice.py  index.html
```
Fix real hits. The only known false positive is the CSS property `white-space:nowrap`
(inside `<style>`) — not the marketing term. Do not rewrite correct CSS to satisfy it.

### 7. Verify in the rendered page
Render headless and actually look at it:
```
<chromium> --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1200,6000 --virtual-time-budget=9000 --screenshot=render.png \
  file://<abs path>/index.html
```
Read the header (date range, "Updated" date, event count), spot-check the cards you
curated, confirm weather chips show on near-term cards. Header hooks that MUST survive:
`data-icon="calendar"`, `data-icon="refresh"`, `id="metaCount"`, and the `nhero` header.

### 7b. Independent review (quality gate — do not skip)
Before Ric sees anything, run a fresh reviewer over the finished page — a subagent (Task
tool) is ideal, so the reviewer isn't the author. Give it the rendered page text and this
explicit checklist, and have it return a list of issues (or "clean"):
- Every event's category matches the rubric (fly-in/show 'n' shine = Cars; members-only PAC
  event ≠ Coffee Creek karaoke; fundraiser banquet = Community; concert = Music).
- No description echoes the raw calendar line; each is one or two warm, plain sentences in
  Ric's voice — no buzzwords, no "not X, it's Y", no salesy lines.
- No truncated venue ("9 a", "260 S") and no run-on or mid-quote title.
- Weather chips present on near-term cards; "· approx." only on outlying towns.
- Header date range, "Updated" date, and event count are correct and consistent.
Fix everything the reviewer flags, then move on. If you can't run a subagent, do this pass
yourself, slowly, reading the whole page — not just the parts you changed.

### 8. Hand it to Ric (no publishing)
- **If the device bridge to Ric's Mac is available**: write `index.html` into
  `/Users/Ric/Documents/GitHub/whats-on-trinity-county/index.html` (device_commit_files).
  It appears as an uncommitted change in GitHub Desktop.
- **If the bridge is NOT available** (his Mac is closed): email him the finished
  `index.html` as an attachment with one line — "save this over
  whats-on-trinity-county/index.html, review in GitHub Desktop, and push."

Either way, send Ric a short note: the window and event count, anything you had to judge,
and the Facebook post (next step). Never state the site is updated — it isn't until he
pushes.

### 9. Facebook post
Draft a short post for this update and include it in the note to Ric. See
`## Facebook post` below for the recipe.

## Voice (from the delivering-work-to-ric skill)

Conversational, warm, concise, confident. Lead with the point. Plain language, natural
sentences, contractions. No buzzwords, no "not X, it's Y" flips, no all-caps labels, no
salesy lines, no emoji unless Ric used them first. Descriptions are for a neighbor, not a
brochure.

## Facebook post

A short reminder-and-notice post, not a launch announcement. The calendar and site are
already known — this says "we refreshed it, here's what's coming."
- 1 short line on what's new/ahead (name 2–4 real draws from this window).
- 1 line that it's the community calendar, updated weekly, free to use and to list on.
- The link: https://trinity-county-events-demo.netlify.app
- Warm, local, no hype. 📅 and 👉 are fine; nothing heavier.

## Known constraints (don't rediscover these)

- Weather APIs (api.weather.gov, open-meteo, wttr.in) are blocked in the sandbox — only the
  NWS `MapClick` page via WebFetch works.
- The cloud session cannot push to the repo (proxy blocks unauthorized repos) — that's why
  publishing routes through Ric's GitHub Desktop, by design.
- `og-image.png` is evergreen (the mountainscape share card) — do not regenerate it weekly.
- The generator's `REGISTRY` and `WEEKLY_TITLE` are the durable home for any categorization
  or title fix — a defect fixed there won't recur. Prefer fixing the generator over
  re-patching output, when a fix is general.
