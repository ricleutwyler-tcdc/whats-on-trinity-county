# What's On in Trinity County

The public community-events site for Trinity County — a collaboration of the **Trinity County Community Development Corporation (TCDC)** and **The Trinity Journal**, part of the *This is Trinity* initiative.

**Live site:** https://events.trinitycommunitydev.org/
(To move to a TCDC subdomain later, attach the subdomain to this same Netlify project so existing links keep working.)

## How it works

- `index.html` — the entire site, a single self-contained file (inline CSS/JS). Generated; don't edit by hand.
- `submit.html` — the "Add your event" form (Netlify Forms), served as /submit.
- `flyer.html` — the printable one-page flyer for the coming week, served as /flyer.
- `events.json` — a public feed of upcoming events that other TCDC sites read (the Revitalization Hub).
- `og-image.png` — the social-preview image referenced by the Open Graph tags in `index.html`.
- `netlify.toml` — publishes the repo root as a static site (no build step), sets the feed's headers, and hides the generator and notes from visitors.
- `generator/` — the weekly rebuild pipeline (see below).

Netlify is linked to this repository: **any commit to the default branch republishes the site automatically.**

## Weekly update

Each Friday The Trinity Journal emails the community calendar. A scheduled Claude job:

1. Reads that week's calendar email.
2. Runs `generator/generate_site.py` to rebuild `index.html`, then curates every new event by hand, adds weather, and rebuilds `flyer.html` and `events.json`.
3. Runs the checks, renders the page at phone, iPad and desktop widths, and opens a pull request with screenshots.
4. Merges it when Ric says "publish"; Netlify republishes.

The full procedure is `generator/WEEKLY_BUILD.md`. Events people submit through the form follow `generator/SUBMISSIONS.md`.

`generator/template.html` is the page shell (brand, header, footer, Open Graph tags). The generator replaces the events data inside it — so edits to branding or meta tags belong in the template, and they carry into every future rebuild.

## Brand

Follows the TCDC Brand 2.0 standard (Trinity Teal, Trinity Gold, Sunset Rust; Georgia headlines + DM Sans body; the *This is Trinity County.* sign-off). See the TCDC brand guidance for the canonical palette and type.
