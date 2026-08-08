# Client preview

Two self-contained pages for sending to a client:

- `index.html` — before / after, drag to wipe between the live page and the rebuild
- `gallery.html` — every section screen by screen, desktop and phone, click to enlarge

Each links to the other, so one URL reaches both.

## Before / after

Compares the live gymcircle.app landing page with the rebuild on this
branch. Everything is inlined — page renders, gallery screenshots and the display
font — so there is no build step and no external request from either page.

## Sending them

Neither page needs a host. Each is a single file with the page renders, the
screenshots and the display font all inlined, and makes no external request, so
it renders the same opened from disk, attached to an email, or dropped on any
static host.

If you do put them on a host, keep them out of search results — both carry a
`noindex` meta tag, and an `X-Robots-Tag: noindex` header on top of that does no
harm.

## Regenerating

The comparison is built from two renders — the live site captured at 1440x900
and the branch rendered at the same size. Both are baked into `index.html`; if
the design changes, the page has to be rebuilt for the "after" half to match.
