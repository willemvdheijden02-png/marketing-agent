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
    '.feature__copy, .feature__media, .third__media, .third__stats, .proof__bar, .founders__quote, .body3d__stage'
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

/* ---------- 6. Hero phone: subtle parallax tilt -------------------------- */
(() => {
  const phone = document.querySelector('[data-tilt]');
  if (!phone || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!matchMedia('(hover:hover) and (min-width:981px)').matches) return;
  addEventListener('pointermove', (e) => {
    const x = (e.clientX / innerWidth - 0.5) * 2;
    const y = (e.clientY / innerHeight - 0.5) * 2;
    phone.style.transform =
      `rotateY(${-14 + x * 7}deg) rotateX(${4 - y * 4}deg) rotateZ(${1 + x}deg)`;
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

/* ---------- 9. The 3D recovery map --------------------------------------
   Loaded only when the section approaches the viewport, and only if WebGL is
   actually available. It sits well below the fold, so it can never delay the
   store buttons or the LCP element.
   -------------------------------------------------------------------------- */
(() => {
  const host = document.querySelector('.js-body3d');
  if (!host) return;

  const readout = document.querySelector('.js-body3d-pick');
  const listBtns = [...document.querySelectorAll('.js-muscle-list button')];

  function bailToImage() {
    host.innerHTML = `<img src="${host.dataset.fallback}" alt="Muscle recovery map showing which groups are ready to train">`;
  }

  function hasWebGL() {
    try {
      const c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
    } catch { return false; }
  }

  if (!hasWebGL()) return bailToImage();

  const io = new IntersectionObserver(async (entries) => {
    // Check every entry, not just the first: a batched callback can deliver
    // the intersecting one in any position.
    if (!entries.some((en) => en.isIntersecting)) return;
    io.disconnect();
    try {
      const { initBody3D } = await import('./body3d.js');
      const api = initBody3D(host, {
        onPick(group, text) {
          if (readout) readout.textContent = text;
          listBtns.forEach((b) => b.classList.toggle('is-active', b.dataset.muscle === group));
          if (group) track('body3d_pick', { muscle: group });
        },
      });
      listBtns.forEach((b) => {
        b.addEventListener('click', () => {
          const same = b.classList.contains('is-active');
          api.setActive(same ? null : b.dataset.muscle);
        });
      });
      track('body3d_loaded');
    } catch (err) {
      console.warn('3D recovery map failed to load, falling back to image', err);
      bailToImage();
    }
  }, { rootMargin: '300px' });

  io.observe(host);
})();
