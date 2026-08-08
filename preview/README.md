# Client preview

Two self-contained pages for sending to a client:

- `index.html` — before / after, drag to wipe between the live page and the rebuild
- `gallery.html` — every section screen by screen, desktop and phone, click to enlarge

Each links to the other, so one URL reaches both.

## Before / after

Compares the live gymcircle.app landing page with the rebuild on this
branch. Everything is inlined — page renders, gallery screenshots and the display
font — so there is no build step and no external request from either page.

## Deploying it

In Vercel: **Add New → Project → import this repo**, then set

- **Root Directory:** `preview`
- **Framework Preset:** Other
- **Build Command:** *(leave empty)*
- **Output Directory:** *(leave empty)*

Deploy. The URL it gives you is the one to send.

Root Directory matters: the repository root also holds `app.py` and other files
that should not be served publicly, and a root deploy would expose them.

`vercel.json` sets `noindex` — this is a client preview, not something that
should turn up in search results next to the real site.

## Deploying the rebuilt landing page too

Same flow, second project, **Root Directory: `gymcircle-site`**. Worth doing:
the five phone screenshots still point at `https://www.gymcircle.app/shots/`,
which resolves fine from the public internet, so a deployed copy shows the real
screenshots rather than the placeholder frames in this comparison.

## Regenerating

The comparison is built from two renders — the live site captured at 1440x900
and the branch rendered at the same size. Both are baked into `index.html`; if
the design changes, the page has to be rebuilt for the "after" half to match.
