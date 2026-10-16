# What's On in Trinity County — guardrails for Claude

The public community-events site for Trinity County (a TCDC + Trinity Journal
collaboration, part of *This is Trinity*). Live at events.trinitycommunitydev.org.
`index.html` is the entire site, and Netlify republishes on every commit to the
default branch. Read `README.md` and `TRAFFIC.md` first.

## Hard rules
- **`index.html` is generated output of `generator/generate_site.py`, which
  rebuilds it weekly from the Trinity Journal calendar.** Prefer changing the
  generator, the categorization rubric, or the known-events registry over
  hand-editing `index.html` — a manual edit is overwritten on the next weekly
  rebuild.
- **Don't break the weekly pipeline.** The generator reads the calendar email
  and regenerates the site; keep its inputs, rubric, and registry intact.
- **Netlify auto-publishes on any commit to the default branch.** So do **not**
  commit to the default branch yourself. Push a feature branch, open a PR; Ric
  reviews and merges, and that merge is the deploy.
- **Keep event and link data accurate**, and don't remove or rename existing
  links in a way that would break URLs people already have.

## Workflow
- Work on a branch; make site changes through the generator, not the output
  HTML; explain changes in the PR.
