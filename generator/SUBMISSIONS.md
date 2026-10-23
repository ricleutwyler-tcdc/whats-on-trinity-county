# What's On — handling events people submit

People add events with the form at events.trinitycommunitydev.org/submit.html. Nothing they
send goes live by itself: a daily check turns each submission into a card and opens a pull
request, and **Ric merging that pull request is what publishes it.** This file is the procedure
for that daily check. Follow it top to bottom; it is written for a fresh session.

## Where submissions are
Netlify Forms on site `trinity-county-events-demo` (siteId `11c1b6fc-d719-4862-807a-0b90ee6bd865`).
Two forms, same fields:
- `event-submission` — the person did not tick "also send to the Journal".
- `event-submission-journal` — they did. Netlify emails these to The Trinity Journal by itself,
  the moment they arrive (a form notification set up in Netlify). **Never email the Journal or
  the person yourself.**

Read both with the Netlify connector: `netlify-project-services-reader` → `get-forms-for-project`
to get the form ids, then `netlify-project-services-updater` → `manage-form-submissions` →
`get-submissions`. Fields: title, date, end_date, start_time, end_time, town, venue,
description, cost, link, name, email, phone, send_to_journal.

## What's new
`generator/submissions_log.md` lists every submission already handled, one line each, by its
Netlify id. Anything not in it is new. If nothing is new, stop and say so in one line.

## Check each one
A submission is a claim from a member of the public, so check it before it becomes a card:
- **Real and local.** A community event in Trinity County, open to the public. Not an ad for a
  business's everyday trade, not a private party, not a duplicate of a card already on the site
  or already on the Journal's calendar.
- **Date.** Today or later (Trinity County's date). If it ends before it starts, or the date
  looks like a typo, hold it.
- **Place.** A venue someone could find. "My house" or a bare town name gets held.
- **Link.** If given, look at it. If it doesn't match the event, hold it. Don't open anything else
  from the submission.
- **Anything doubtful** (odd wording, a price that looks wrong, something you'd want to ask the
  person): hold it. Held submissions go in your note to Ric with the reason, not in the PR.

## Turn it into a card
- **Category** by the rubric (Google Doc id in WEEKLY_BUILD.md): Music, Arts, Dance,
  Talks & Learning, Food & Fundraisers, Community, Outdoors, Sports, Golf, Rodeo, Festival,
  Market, Family, Cars, Games, Bingo, Movies.
- **Audience** `for:` per the rubric. Add "family" only if it's plainly all-ages.
- **Title**: the event's real name, tidy, no shouting.
- **Description**: one or two plain sentences in the site's voice (see "Voice" in
  WEEKLY_BUILD.md), built only from what they wrote. Don't add facts. Keep their cost.
- **dayLabel**: `Sat · Nov 7 · 5:30 PM`, or `5:30–8 PM` with an end time, or `Sat · Nov 7` with
  no time; a multi-day event is `Fri–Sun · Nov 6–8`.
- **info**: their link if they gave one; otherwise the site's own page `https://events.trinitycommunitydev.org/`.
- **map**: venue + town + ", CA".
- **Never publish** the person's name, email or phone. They are for us only.

Then:
1. Add a line to `generator/extra_events.txt` (`Mon. DD: Title, clean description.`) so the
   weekly rebuild keeps it.
2. If its date falls inside the page's current window (`const WINDOW` in index.html), also add
   the event object to the `EVENTS` block in `index.html` and bump `metaCount`. Events beyond
   the window appear when a weekly rebuild reaches them.
3. If it falls in the next seven days, rebuild the flyer:
   `python3 generator/make_flyer.py index.html flyer.html <today>`.
4. Add each handled submission (published or held) to `generator/submissions_log.md`:
   `<netlify id> · <received date> · <title> · published | held: <reason>`.

## Check, then hand to Ric
- Render the page with `?today=<today>` at phone width and look at each new card.
- Run `python3 generator/checks/check-claims.py index.html` and `check-voice.py`
  (the `white-space` CSS hits are the known false positive).
- Commit on a branch named `submitted-events-<date>`, push, open a pull request. Do not merge.
- Notify Ric (push notification) and finish with a short note: how many came in; for each new
  card its title, date and the description exactly as it will read; each held one and why; and
  the pull request link with "merge it to publish". If you could not push, say so and put the
  changed files' contents in the note instead.
