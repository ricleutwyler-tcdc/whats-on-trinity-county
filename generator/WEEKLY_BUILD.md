# What's On in Trinity County — Weekly Build Runbook

This is the exact procedure the weekly scheduled task follows to rebuild the site from
Wayne Agner's Trinity Journal calendar. Follow it top to bottom. It is written to be run
by a fresh session with no memory of prior weeks.

## Non-negotiables (read first)

1. **Nothing publishes without Ric's "publish".** Never commit to `main` directly. Your
   job ends at a pull request plus screenshots for Ric. When he says "publish", merge it
   yourself (step 8). His look at the screenshots is the safety gate — keep it. Don't
   ask him to merge or to use GitHub Desktop.
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
- **The repo**: `https://github.com/ricleutwyler-tcdc/whats-on-trinity-county`. Work on a
  branch named `weekly-YYYY-MM-DD` (today's date). On Ric's Mac, push with `gh`'s login
  (see CLAUDE.md); a cloud session needs the repo attached with push access.
- **The build tools** (in the repo under `generator/`): `generate_site.py`,
  `inject_weather.py`, `template.html`, `curate_overrides.py` (example), and
  `checks/check-claims.py`, `checks/check-voice.py`.
- **The rubric** (categorization + registry source of truth): Google Drive doc
  `1jyWlfqJnY3aTtc_sDQ41uEFw1wuXu1drzxQFnGm9XFM`. The same rules are mirrored in the
  `REGISTRY` inside `generate_site.py`.
  To change the rubric, don't ask Ric to edit it: the Drive connector can't edit a doc's
  body, so write the whole corrected rubric as a new Google Doc with the same title in the
  same folder (`1mC9tI9IUInLM2F6g4CqPDR-6n0EvOXn0`), read it back to confirm nothing was
  lost, put the new ID above, and retitle the old one "SUPERSEDED …" (don't trash it).
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

Then check nobody has built this week already: `gh pr list --state all --limit 5`. On
Oct 30, 2026 two sessions built the same week and had to be combined by hand. If an open
pull request for this calendar exists, build on its branch or tell Ric, rather than
starting a second one.

### 2. Get the build tools
Start a branch from the latest `main`.

**Ride-alongs (saves Netlify credits).** Every merge to `main` that changes the public site
is a production deploy, and each costs Netlify credits; previews are free. So small changes
wait for the weekly build instead of getting their own deploy. List them with
`gh pr list --label ride-along --state open`. For each one that is not a draft, merge its
branch into this week's branch (`git merge --no-ff origin/<its branch>`). If it conflicts or
breaks a check, leave it out and say so. Name each in the weekly PR description
("Also ships: #N, title"). After the weekly PR is merged, close each ride-along with a
comment pointing to it. A draft ride-along is not ready: leave it alone. Use `generator/generate_site.py`,
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
  **Food & Fundraisers**; a hike or cleanup is **Outdoors**; a talk or class is **Talks & Learning**. When in doubt, the rubric doc wins; if you make a new call, note it for
  Ric so it can be folded into the rubric.
- **Audience** — members-only → locals only; a countywide festival → visitor/local/family.

Events people submit through the site's form (see `SUBMISSIONS.md`) are already checked and
written, and sit in `extra_events.txt`. Keep their wording as it is unless something is wrong.

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

### 5b. Flyer
```
python3 make_flyer.py index.html flyer.html <today YYYY-MM-DD>
```
Writes `flyer.html`, a one-page printable list of the next seven days with a QR code to the
site (`flyer-qr.svg`; the address never changes, so the QR doesn't either). The site's
"Print this week's flyer" button opens it. It uses the curated text as-is, so run it after
curation and weather. Open it and check it fits one page; it shrinks its type when the week is
busy. Hand `flyer.html` to Ric with `index.html` — it belongs in the repo root next to it.

### 5c. events.json
```
python3 export_events.py index.html ../events.json <today YYYY-MM-DD>
```
Writes `events.json` at the repo root: every dated event from today on (weekly fixtures
skipped), with date, day label, title, place, town, category and a link to its card. Other
TCDC sites read it (the Revitalization Hub's Event support page), so run it whenever
`index.html` changes, alongside the flyer. Read the town it printed for each event: a place
that names no town shows as "Other"; if it's a regular venue, add it to `VENUES` in the script.

### 6. Checkers
```
python3 checks/check-claims.py index.html
python3 checks/check-voice.py  index.html
python3 checks/check-colours.py index.html
```
`check-colours.py` checks the card category colours (`CAT_FILL` in the template): white text
clears 4.5:1 on every fill, no two fills closer than ΔE 20, at most nine fills (Brand 2.0 §2a).
A new category with no entry in `CAT_FILL` shows in Deep Teal; add it there if it needs its own colour.
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
  event ≠ Coffee Creek karaoke; fundraiser banquet = Food & Fundraisers; hike/cleanup = Outdoors; talk/class = Talks & Learning; concert = Music).
- No description echoes the raw calendar line; each is one or two warm, plain sentences in
  Ric's voice — no buzzwords, no "not X, it's Y", no salesy lines.
- No truncated venue ("9 a", "260 S") and no run-on or mid-quote title.
- Weather chips present on near-term cards; "· approx." only on outlying towns.
- Header date range, "Updated" date, and event count are correct and consistent.
Fix everything the reviewer flags, then move on. If you can't run a subagent, do this pass
yourself, slowly, reading the whole page — not just the parts you changed.

### 8. Hand it to Ric, then publish on his word
Commit `index.html`, `flyer.html` and `events.json` on the weekly branch, push it, and
open a pull request against `main` (`gh pr create`). Send Ric a short note: the pull
request link, screenshots at phone, iPad and desktop widths, the window and event count,
anything you had to judge, and the Facebook post (next step).

When he says "publish": `gh pr merge <n> --merge`, then wait for the live site to show the
new window and "Updated" date (Netlify takes under a minute) and tell him it's live. Never
say the site is updated before that.

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
- **Check every date before you write it.** For each event you name, confirm its date
  against the calendar AND against today. Never call an event "yesterday," "today," "this
  weekend," "final day," or "next weekend" without checking today's date against the event's
  actual date. A wrong "final day / last weekend" claim is exactly the kind of public error
  a reader will correct in the comments. When unsure, name the date outright ("Sept 18–20")
  instead of a relative day.
- 1 line that it's the community calendar, updated weekly, free to use and to list on.
- The link: use this EXACT canonical URL — https://events.trinitycommunitydev.org
  NEVER a Gmail/redirect-wrapped version (anything like `https://www.google.com/url?q=...`).
  If you copied the link from an email, strip it back to the canonical URL above.
- Warm, local, no hype. 📅 and 👉 are fine; nothing heavier.

## Known constraints (don't rediscover these)

- Weather APIs (api.weather.gov, open-meteo, wttr.in) are blocked in the sandbox — only the
  NWS `MapClick` page via WebFetch works.
- Netlify deploys every commit to `main`, so publishing goes through a pull request that is
  merged only on Ric's "publish".
- The generator drops a calendar line that continues on the next line (Oct 30: the
  Veterans Day breakfast). Read the raw calendar around each event you curate.
- `og-image.png` is evergreen (the mountainscape share card) — do not regenerate it weekly.
- The generator's `REGISTRY` and `WEEKLY_TITLE` are the durable home for any categorization
  or title fix — a defect fixed there won't recur. Prefer fixing the generator over
  re-patching output, when a fix is general.
