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
  commit to the default branch directly. Push a feature branch, open a PR, and
  show Ric screenshots (phone, iPad, desktop). When he says "publish", merge the
  PR yourself (`gh pr merge <n> --merge`); that merge is the deploy. Then check
  the live site and tell him it's live. Don't hand him GitHub Desktop steps or
  ask him to merge.
- **Keep event and link data accurate**, and don't remove or rename existing
  links in a way that would break URLs people already have.

## Workflow
- Work on a branch; make site changes through the generator, not the output
  HTML; explain changes in the PR.
- On Ric's Mac, `gh` is at `~/.local/bin/gh`, signed in as ricleutwyler-tcdc.
  Plain `git push` has no login; push with
  `git -c credential.helper= -c credential.helper='!gh auth git-credential' push -u origin <branch>`.

## TCDC design standards
This site is part of the TCDC family and follows the shared TCDC design system
(canonical copy: `ricleutwyler-tcdc/tcdc-brand` → `tcdc-design-system.md`,
`tcdc-footer.js`). Reuse the system; don't reinvent shared UI.
- **This site:** site key `whats-on` · accent `#D89311`.
- **Footer — use the shared component, never build one:** load
  `https://trinitycommunitydev.org/tcdc-footer.js` and place
  `<tcdc-footer site="whats-on"></tcdc-footer>`. To change the footer, edit the
  component in the brand repo, not per site. This site's own footer content (just the
  "Report a problem" link) goes inside the element, in
  `generator/template.html`; the "Sources & how this was built" note lives on
  `about.html`. Don't put the collaboration
  line or the updates sign-up there; the component renders those.
- **Standards:** shell stays identical across sites, only the per-site signature
  changes; UX baseline (real type scale, 8px spacing, WCAG AA contrast, full
  width with body text ≤68ch, one primary action); usability beats brand
  decoration; don't build pages or footers as artifacts; show Ric a rendered
  mockup before building or deploying anything new.
