# What's On in Trinity County

The public community-events site for Trinity County — a collaboration of the **Trinity County Community Development Corporation (TCDC)** and **The Trinity Journal**, part of the *This is Trinity* initiative.

**Live site:** https://trinity-county-events-demo.netlify.app/
(To move to a TCDC subdomain later, attach the subdomain to this same Netlify project so existing links keep working.)

## How it works

- `index.html` — the entire site, a single self-contained file (inline CSS/JS). This is what Netlify publishes.
- `og-image.png` — the social-preview image referenced by the Open Graph tags in `index.html`.
- `netlify.toml` — tells Netlify to publish the repo root as a static site (no build step).
- `generator/` — the weekly rebuild pipeline (see below).

Netlify is linked to this repository: **any commit to the default branch republishes the site automatically.** No manual upload, no browser needed.

## Weekly update (hands-off)

Each week The Trinity Journal sends the community calendar. The process:

1. A scheduled task reads that week's calendar email.
2. `generator/generate_site.py` rebuilds `index.html` from the calendar, using the categorization rubric and known-events registry for accurate categories and human-quality descriptions.
3. The rebuilt `index.html` is committed to this repo.
4. Netlify republishes automatically.

`generator/template.html` is the page shell (brand, header, footer, Open Graph tags). The generator replaces the events data inside it — so edits to branding or meta tags belong in the template, and they carry into every future rebuild.

## Brand

Follows the TCDC Brand 2.0 standard (Trinity Teal, Trinity Gold, Sunset Rust; Georgia headlines + DM Sans body; the *This is Trinity County.* sign-off). See the TCDC brand guidance for the canonical palette and type.
