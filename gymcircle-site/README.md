# GymCircle landing page — rebuilt

A drop-in replacement for the `gymcircle.app` home page. Static HTML/CSS/JS,
**no build step, no framework, no CDN calls**. Copy the folder contents to the
site root and it runs.

The design language of the live site is deliberately kept — near-black,
orange, condensed display type. What changed is the stuff that was costing
downloads.

---

## What changed, and what each change is for

| Change | Why it earns its place |
|---|---|
| **Body text contrast raised** (`#8a8580` → `#C4BCB2`, 4.0:1 → 10.4:1) | The old page failed WCAG AA on almost every paragraph. Low contrast is the single biggest reason a page reads as "generic" — and it's the cheapest thing on this list to fix. |
| **Fake CSS app-cards replaced with real app UI** | Sections 01 and 03 previously re-created the app in HTML at 10–11px, dark-on-dark. On a phone they were unreadable. Real screenshots and clips show a product that works. |
| **Video slots everywhere a mockup used to be** | The pitch is live counts, streaks and PR celebrations. Motion proves it; a static PNG asks people to take your word for it. |
| **Desktop QR code** (hero + modal) | The old page gave desktop visitors two store buttons they physically could not tap. That was a dead end for every laptop visitor. |
| **Third-space section promoted from last to third** | It's the one thing no competitor has. It was buried under table-stakes features. |
| **Interactive 3D recovery map** | The only 3D on the page, and the only visual that carries information a flat image can't: recovery state is per muscle, and muscles are on all sides of a body. Front shows chest/delts hot; spin it and you see traps, lats, hamstrings. |
| **CSS-3D "circle" orbit** | Makes the product's central noun literal, and puts people (initials) on a page about training with people. Pure CSS — no library. |
| **Analytics on every CTA + scroll depth** | Without it, "did the redesign work?" is unanswerable. Vendor-agnostic: fires into GA4, Plausible, PostHog or dataLayer, whichever is present. |
| **Self-hosted display font** (Anton, 19KB) | No Google Fonts request — faster, and no third-party call from an EU-facing page. |
| **Accessible FAQ, skip link, focus rings, reduced-motion support** | Keyboard and screen-reader users could not operate the old accordion. |
| **Proof bar with verifiable numbers only** | See "Reviews" below — nothing invented ships as social proof. |

---

## Deploy

Any static host. Drop the contents at the web root:

```
index.html
assets/
favicon.svg          ← keep your existing one
privacy.html         ← keep your existing ones
delete.html
shots/               ← see "Assets" below
```

Vercel / Netlify / Cloudflare Pages: point at this directory, no build command,
output directory `.`.

Local preview:

```bash
python3 -m http.server 8080     # then open http://localhost:8080
```

---

## Assets — the two things to finish

### 1. Screenshots (works today, but pointing at the live domain)

Images currently reference `https://www.gymcircle.app/shots/*.png` absolutely,
so the page renders correctly the moment you open it. **Before going live,
copy your existing `/shots` folder next to `index.html` and search-replace
`https://www.gymcircle.app/shots/` → `shots/`** so the page stops depending on
the old deployment.

The frames reserve space with `aspect-ratio: 9/19.5` (phone screenshots). If
your assets are a different shape, adjust `.shot .media` in `styles.css` —
that ratio is what prevents layout shift while images load.

### 2. Video clips (the highest-value thing still missing)

Every mockup slot is a `<video>` whose `poster` is the real screenshot. If the
clip file is absent, **the screenshot stays and nothing breaks** — so the page
is shippable right now and gets better the day you drop clips in.

Record these as silent screen captures, 6–10s, looping, MP4 (H.264), ≤2MB
each, and drop them here:

```
clips/train.mp4      hero — a set being logged, rest timer starting
clips/logging.mp4    section 01 — two taps, numbers pre-filled
clips/pr.mp4         section 05 — a PR firing, crew reacting
```

Nothing else to wire up; they're picked up automatically.

---

## Reviews — deliberately empty

`REVIEWS` at the top of `assets/js/main.js` is an empty array, and the reviews
block stays hidden until it's filled. **This is on purpose: no invented
testimonials ship from here.** Paste real App Store reviews in and the section
appears:

```js
const REVIEWS = [
  { stars: 5, text: "…", author: "— name, App Store" },
];
```

Only verifiable claims (★5.0, 5,000+ downloads, free, both stores) render by
default.

---

## Analytics

`track()` in `main.js` is vendor-agnostic — add your snippet to `<head>` and
events flow automatically. Events emitted:

`nav_get_app`, `hero_appstore`, `hero_googleplay`, `final_appstore`,
`final_googleplay`, `modal_appstore`, `modal_googleplay`, `final_qr`,
`faq_open`, `body3d_loaded`, `body3d_pick`, `scroll_depth` (25/50/75/100)

**The number that matters is store-button clicks per visitor.** That's the
kill criterion: if it hasn't moved two weeks after launch, the bottleneck is
traffic, not the page — stop polishing and build the SEO/gym-pages layer
instead.

---

## Performance notes

- `three.js` (vendored, ~170KB gzipped) is **dynamically imported only when the
  recovery section approaches the viewport**, and only if WebGL is present. It
  sits well below the fold, so it can never delay the store buttons or the LCP
  element.
- No WebGL, or the module fails to load → the section falls back to the
  existing `recovery-body.png` automatically.
- `prefers-reduced-motion` disables auto-rotation, the pulse, the marquee, the
  parallax tilt and all reveals. The figure stays draggable.
- Clips play only while on screen and pause when scrolled past or the tab is
  hidden.
- The 3D render loop stops entirely when the section leaves the viewport.

## Browser support

Chrome/Edge/Safari/Firefox current. Uses ES modules, `IntersectionObserver`,
`ResizeObserver`, `aspect-ratio` and `color-mix()`. Older browsers get the page
without the 3D map and without the frosted nav — everything else works.

## Third-party

| Package | Licence | Where |
|---|---|---|
| three.js 0.169 | MIT | `assets/vendor/three.module.min.js` |
| qrcode-generator 1.4.4 | MIT | `assets/vendor/qrcode.js` |
| Anton | OFL 1.1 | `assets/fonts/` |

Licence texts sit next to each file. Swap Anton for GymCircle's own licensed
condensed face if there is one — the stylesheet only ever refers to
`--font-display`.
