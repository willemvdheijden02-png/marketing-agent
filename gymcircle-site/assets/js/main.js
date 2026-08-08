/* ==========================================================================
   main.js — page behaviour
   No framework, no build step. Everything heavy is loaded on demand.
   ========================================================================== */

/* --------------------------------------------------------------------------
   REAL App Store reviews go here. Left empty on purpose: the reviews block
   stays hidden until you paste genuine ones in, so nothing invented ever
   ships as social proof. Shape: { stars, text, author }
   -------------------------------------------------------------------------- */
const REVIEWS = [
  // { stars: 5, text: "…", author: "— name, App Store" },
];

/* Set to true only by the design-preview build, which fills REVIEWS with
   placeholders. It makes the block render a "not real reviews" notice, so a
   preview can never be mistaken for shipped social proof. Ships as false. */
const REVIEWS_ARE_SAMPLES = false;

/* ---------- 1. Analytics ---------------------------------------------------
   Vendor-agnostic. Fires into GA4 (gtag), Plausible, PostHog or dataLayer —
   whichever is present. Without this, "did the redesign work?" is unanswerable,
   which was the single biggest gap on the old page.
   -------------------------------------------------------------------------- */
function track(name, props = {}) {
  try {
    if (typeof window.gtag === 'function') window.gtag('event', name, props);
    if (typeof window.plausible === 'function') window.plausible(name, { props });
    if (window.posthog?.capture) window.posthog.capture(name, props);
    (window.dataLayer ||= []).push({ event: name, ...props });
  } catch (_) { /* never let analytics break the page */ }
}

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-track]');
  if (el) track(el.dataset.track, { href: el.getAttribute('href') || undefined });
});

// How far down do people actually get?
(() => {
  const marks = [25, 50, 75, 100];
  const seen = new Set();
  addEventListener('scroll', () => {
    const pct = (scrollY + innerHeight) / document.body.scrollHeight * 100;
    for (const m of marks) if (pct >= m && !seen.has(m)) { seen.add(m); track('scroll_depth', { depth: m }); }
  }, { passive: true });
})();

/* ---------- 2. Media: video clips with screenshot fallback -----------------
   Every video slot points at a clip that may not exist yet. If it is missing
   or fails, the real app screenshot in `poster` stays put. The page is
   shippable today and gets better the day clips land in /clips.
   -------------------------------------------------------------------------- */
/* Which clips actually exist in /clips. Empty means every video slot renders
   as its poster screenshot — no requests, no 404s in the console. Add the
   filename here the day you drop the file in and that slot starts playing:

     const AVAILABLE_CLIPS = new Set(['clips/train.mp4']);                     */
const AVAILABLE_CLIPS = new Set([]);

document.querySelectorAll('video[data-clip]').forEach((video) => {
  const src = video.dataset.clip;

  // Not shot yet: keep the poster frame visible as a plain image.
  if (!AVAILABLE_CLIPS.has(src)) {
    const img = new Image();
    img.src = video.poster;
    img.alt = video.getAttribute('aria-label') || '';
    img.loading = 'lazy';
    img.className = video.className;
    video.replaceWith(img);
    return;
  }

  const s = document.createElement('source');
  s.src = src; s.type = 'video/mp4';
  video.appendChild(s);
  video.load();
  video.dataset.hasClip = 'true';

  // A listed clip that still fails to load falls back to the poster too.
  video.addEventListener('error', () => {
    const img = new Image();
    img.src = video.poster;
    img.alt = video.getAttribute('aria-label') || '';
    img.className = video.className;
    video.replaceWith(img);
  }, { once: true });
});

// Play clips only while visible — saves battery, keeps scroll smooth.
const playObserver = new IntersectionObserver((entries) => {
  for (const en of entries) {
    const v = en.target;
    if (v.dataset.hasClip !== 'true') continue;
    en.isIntersecting ? v.play().catch(() => {}) : v.pause();
  }
}, { threshold: 0.35 });
document.querySelectorAll('video[data-autoplay-in-view]').forEach((v) => playObserver.observe(v));

/* ---------- 3. Sticky nav state ------------------------------------------ */
const nav = document.getElementById('nav');
addEventListener('scroll', () => nav.classList.toggle('is-stuck', scrollY > 12), { passive: true });

/* ---------- 4. Scroll reveal --------------------------------------------- */
(() => {
  const targets = document.querySelectorAll(
    '.feature__copy, .feature__media, .third__media, .third__stats, ' +
    '.proof__bar, .proof__reviews, .founders__quote, .bodymap__stage'
  );
  targets.forEach((el) => el.setAttribute('data-reveal', ''));
  const io = new IntersectionObserver((entries) => {
    for (const en of entries) if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
  }, { threshold: 0.12, rootMargin: '0px 0px -60px' });
  targets.forEach((el) => io.observe(el));
})();

/* ---------- 5. FAQ accordion (keyboard + screen-reader safe) -------------- */
document.querySelectorAll('.acc__btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const item = btn.closest('.acc__item');
    const open = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!open));
    item.classList.toggle('is-open', !open);
    if (!open) track('faq_open', { q: btn.textContent.trim() });
  });
});

/* ---------- 6. Hero scene: parallax tilt ---------------------------------
   The phone rotates; the two UI cards translate by their own data-depth, so
   they part from the handset as the pointer moves instead of tracking it
   rigidly. That difference in rate is the whole illusion of depth.
   -------------------------------------------------------------------------- */
(() => {
  const phone = document.querySelector('[data-tilt]');
  if (!phone || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!matchMedia('(hover:hover) and (min-width:981px)').matches) return;

  const floats = [...document.querySelectorAll('.float[data-depth]')];
  let queued = false, px = 0, py = 0;

  const paint = () => {
    queued = false;
    phone.style.transform =
      `rotateY(${-14 + px * 7}deg) rotateX(${4 - py * 4}deg) rotateZ(${1 + px}deg)`;
    for (const f of floats) {
      const d = Number(f.dataset.depth) || 0;
      // `transform`, because the idle bob animation owns `translate` and a
      // running animation outranks inline style for the property it animates.
      // Keeps the 70px of Z that lifts the card clear of the handset.
      f.style.transform = `translate3d(${-px * d}px, ${-py * d * 0.55}px, 70px)`;
    }
  };

  addEventListener('pointermove', (e) => {
    px = (e.clientX / innerWidth - 0.5) * 2;
    py = (e.clientY / innerHeight - 0.5) * 2;
    if (!queued) { queued = true; requestAnimationFrame(paint); }
  }, { passive: true });
})();

/* ---------- 7. Reviews (only if real ones are supplied) ------------------ */
(() => {
  if (!REVIEWS.length) return;
  const host = document.querySelector('.js-reviews');
  host.hidden = false;
  host.innerHTML = REVIEWS.map((r) => `
    <figure class="review">
      <div class="review__stars" aria-label="${r.stars} out of 5">${'★'.repeat(r.stars)}</div>
      <p>${r.text}</p>
      <cite>${r.author}</cite>
    </figure>`).join('');

  // Design previews fill REVIEWS with placeholders so the block can be seen.
  // Anything not from the App Store has to say so, on the page, next to it.
  if (REVIEWS_ARE_SAMPLES) {
    const note = document.createElement('p');
    note.className = 'proof__sample';
    note.innerHTML = '<b>Sample</b> Placeholder layout — not real reviews. '
      + 'The block stays hidden until genuine App Store reviews are pasted in.';
    host.after(note);
  }
})();

/* ---------- 8. QR codes + modal ------------------------------------------ */
(async () => {
  const holders = document.querySelectorAll('.js-qr-canvas');
  if (!holders.length) return;
  const { default: qrcode } = await import('../vendor/qrcode.js');
  holders.forEach((el) => {
    const qr = qrcode(0, 'M');
    qr.addData(el.dataset.qr);
    qr.make();
    el.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
    const svg = el.querySelector('svg');
    if (svg) { svg.setAttribute('width', '100%'); svg.setAttribute('height', '100%'); }
  });
})();

(() => {
  const modal = document.getElementById('qr-modal');
  if (!modal) return;
  let lastFocus = null;
  const open = () => {
    lastFocus = document.activeElement;
    modal.hidden = false;
    modal.querySelector('.modal__x').focus();
    document.body.style.overflow = 'hidden';
  };
  const close = () => {
    modal.hidden = true;
    document.body.style.overflow = '';
    lastFocus?.focus();
  };
  document.querySelectorAll('.js-qr-open').forEach((b) => b.addEventListener('click', open));
  document.querySelectorAll('.js-qr-close').forEach((b) => b.addEventListener('click', close));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) close(); });
})();

/* ---------- 8b. Gym map filter -------------------------------------------
   The map is correct with JavaScript off — every pin renders. This only adds
   the three chips, which dim the pins they exclude rather than removing them,
   so the map keeps its shape while you switch.
   -------------------------------------------------------------------------- */
(() => {
  const map = document.querySelector('.js-map');
  if (!map) return;
  const chips = [...map.querySelectorAll('.map__chip')];
  const pins = [...map.querySelectorAll('.pin[data-kind]')];

  const apply = (filter) => {
    map.classList.toggle('map--filtered', filter !== 'all');
    for (const p of pins) p.classList.toggle('is-shown', filter === 'all' || p.dataset.kind === filter);
    for (const c of chips) c.classList.toggle('is-on', c.dataset.filter === filter);
  };

  for (const chip of chips) {
    chip.addEventListener('click', () => {
      apply(chip.dataset.filter);
      track('gymmap_filter', { filter: chip.dataset.filter });
    });
  }
  apply('all');
})();

/* ---------- 9. The recovery body map -------------------------------------
   The map itself is inline SVG with the recovery state baked into its
   classes, so it renders correctly with JavaScript off. This only adds the
   tapping. Wire MUSCLE_STATE to real per-user data if this ever renders
   logged in; as marketing copy it shows a realistic mid-week state (a push
   day two days ago) rather than an empty board.
   -------------------------------------------------------------------------- */
const MUSCLE_STATE = {
  chest: 'worked', shoulders: 'worked', triceps: 'worked',
  traps: 'ready', lats: 'ready', biceps: 'ready', abs: 'ready',
  obliques: 'ready', glutes: 'ready', quads: 'ready',
  hamstrings: 'ready', calves: 'ready',
};

const MUSCLE_NAMES = {
  chest: 'Chest', shoulders: 'Shoulders', triceps: 'Triceps', traps: 'Traps',
  lats: 'Lats', biceps: 'Biceps', abs: 'Abs', obliques: 'Obliques',
  glutes: 'Glutes', quads: 'Quads', hamstrings: 'Hamstrings', calves: 'Calves',
};

/* The six chips map onto those twelve groups. */
const REGIONS = {
  chest: ['chest'],
  back: ['lats', 'traps'],
  shoulders: ['shoulders'],
  arms: ['biceps', 'triceps'],
  core: ['abs', 'obliques'],
  legs: ['glutes', 'quads', 'hamstrings', 'calves'],
};
const REGION_NAMES = {
  chest: 'Chest', back: 'Back', shoulders: 'Shoulders',
  arms: 'Arms', core: 'Core', legs: 'Legs',
};

(() => {
  const figs = document.querySelector('.js-bodymap');
  if (!figs) return;

  const readout = document.querySelector('.js-bodymap-pick');
  const chips = [...document.querySelectorAll('.js-muscle-list button')];
  const shapes = [...figs.querySelectorAll('.m')];

  const total = Object.keys(MUSCLE_STATE).length;
  const readyCount = Object.values(MUSCLE_STATE).filter((s) => s === 'ready').length;
  const summary = `${readyCount} of ${total} muscle groups ready to train`;

  const regionOf = (muscle) =>
    Object.keys(REGIONS).find((r) => REGIONS[r].includes(muscle)) || null;

  let active = null;

  /**
   * @param {string|null} region     one of REGIONS, or null to clear
   * @param {string} [preciseName]   specific muscle name when tapped on the body
   * @param {string} [preciseState]
   */
  function setActive(region, preciseName, preciseState) {
    active = region;
    const groups = region ? REGIONS[region] : [];

    figs.classList.toggle('has-selection', !!region);
    for (const s of shapes) s.classList.toggle('is-active', groups.includes(s.dataset.muscle));
    for (const c of chips) c.classList.toggle('is-active', c.dataset.muscle === region);

    if (!readout) return;
    if (!region) { readout.textContent = summary; return; }

    const name = preciseName || REGION_NAMES[region];
    const state = preciseState
      || (groups.some((g) => MUSCLE_STATE[g] === 'worked') ? 'worked' : 'ready');
    readout.textContent = state === 'worked'
      ? `${name} — still recovering, give it a day`
      : `${name} — fresh, good to train today`;
  }

  for (const shape of shapes) {
    shape.addEventListener('click', () => {
      const muscle = shape.dataset.muscle;
      const region = regionOf(muscle);
      // Tapping the selected group again clears it.
      if (region && region === active) return setActive(null);
      // Name the exact muscle tapped, but light up its whole region.
      setActive(region, MUSCLE_NAMES[muscle], MUSCLE_STATE[muscle]);
      track('bodymap_pick', { muscle });
    });
  }

  for (const chip of chips) {
    chip.addEventListener('click', () => {
      const region = chip.dataset.muscle;
      setActive(region === active ? null : region);
      if (region !== active) track('bodymap_pick', { muscle: region });
    });
  }

  // Tapping the empty space around the figures clears the selection.
  figs.addEventListener('click', (e) => { if (!e.target.closest('.m')) setActive(null); });

  setActive(null);
})();
