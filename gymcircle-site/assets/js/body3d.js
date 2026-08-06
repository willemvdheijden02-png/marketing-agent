/* ==========================================================================
   body3d.js — the interactive recovery map
   --------------------------------------------------------------------------
   Why this is the only piece of 3D on the page: it is the one visual here
   that carries information a flat image cannot. Recovery state is per muscle,
   and muscles sit on all sides of a body — so the object genuinely wants to
   be rotatable. Everything else is better served by a real screenshot or a
   video clip of the app.

   Built from primitives, so there is no model file to download and every
   muscle is its own mesh that can be coloured by state. ~35 low-poly meshes,
   no shadow maps, no post-processing: cheap enough for a mid-range phone.
   ========================================================================== */

import * as THREE from '../vendor/three.module.min.js';

/* The app tracks twelve groups; so does this. Wire to real per-user data if
   this ever renders logged-in — as marketing copy it shows a realistic
   mid-week state (a push day two days ago) rather than an empty board. */
export const MUSCLE_STATE = {
  chest:      'worked',
  shoulders:  'worked',
  triceps:    'worked',
  traps:      'ready',
  lats:       'ready',
  biceps:     'ready',
  abs:        'ready',
  obliques:   'ready',
  glutes:     'ready',
  quads:      'ready',
  hamstrings: 'ready',
  calves:     'ready',
};

const NAMES = {
  chest: 'Chest', shoulders: 'Shoulders', triceps: 'Triceps', traps: 'Traps',
  lats: 'Lats', biceps: 'Biceps', abs: 'Abs', obliques: 'Obliques',
  glutes: 'Glutes', quads: 'Quads', hamstrings: 'Hamstrings', calves: 'Calves',
};

/* The six chips in the copy column map onto those twelve groups. */
export const REGIONS = {
  chest:     ['chest'],
  back:      ['lats', 'traps'],
  shoulders: ['shoulders'],
  arms:      ['biceps', 'triceps'],
  core:      ['abs', 'obliques'],
  legs:      ['glutes', 'quads', 'hamstrings', 'calves'],
};
const REGION_NAMES = {
  chest: 'Chest', back: 'Back', shoulders: 'Shoulders',
  arms: 'Arms', core: 'Core', legs: 'Legs',
};

const COLOR = {
  ready:     { base: 0x1E9770, emissive: 0x19C48C },
  worked:    { base: 0xC2410C, emissive: 0xFF4D0F },
  structure: { base: 0x5C534B, emissive: 0x000000 },
};

export function initBody3D(container, { onPick } = {}) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(container.clientWidth, container.clientHeight, false);
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, container.clientWidth / container.clientHeight, 0.1, 50);
  camera.position.set(0, 0.02, 3.7);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x140F0C, 0.55));
  const key  = new THREE.DirectionalLight(0xfff3ea, 1.25); key.position.set(2.5, 3.5, 4);   scene.add(key);
  const rim  = new THREE.DirectionalLight(0xff6a2b, 0.8);  rim.position.set(-3.5, 1.2, -2.5); scene.add(rim);
  const fill = new THREE.DirectionalLight(0x9ec4ff, 0.3);  fill.position.set(-2.2, -1.5, 2);  scene.add(fill);

  const figure = new THREE.Group();
  figure.position.y = 0.02;
  figure.rotation.y = -0.38;   // start on a three-quarter view, not flat-on
  scene.add(figure);

  /* ---- materials: one per state, shared by every mesh in that state ---- */
  const materials = {};
  function mat(state) {
    if (!materials[state]) {
      const c = COLOR[state] || COLOR.structure;
      materials[state] = new THREE.MeshStandardMaterial({
        color: c.base, emissive: c.emissive,
        emissiveIntensity: state === 'structure' ? 0 : 0.3,
        roughness: state === 'structure' ? 0.85 : 0.45,
        metalness: 0.05,
      });
    }
    return materials[state];
  }

  const groupMeshes = {};                       // muscle key -> [mesh]
  const cap = (r, len) => new THREE.CapsuleGeometry(r, len, 4, 16);
  const sph = (r) => new THREE.SphereGeometry(r, 20, 14);

  function add(geo, pos, group, rot, scale) {
    const state = group ? (MUSCLE_STATE[group] || 'ready') : 'structure';
    const m = new THREE.Mesh(geo, mat(state));
    m.position.set(pos[0], pos[1], pos[2]);
    if (rot) m.rotation.set(rot[0] || 0, rot[1] || 0, rot[2] || 0);
    if (scale) m.scale.set(scale[0], scale[1], scale[2]);
    m.userData.group = group || null;
    m.userData.baseScale = m.scale.clone();
    figure.add(m);
    if (group) (groupMeshes[group] ||= []).push(m);
    return m;
  }

  /* ---- the figure -------------------------------------------------------
     Stylised, not anatomical. Readable at thumbnail size beats accurate:
     a structural body mass in neutral grey, with the twelve tracked muscle
     groups sitting on top of it in their recovery colour.
     ------------------------------------------------------------------------ */

  // Structure: head, neck, torso mass, hips, forearms, hands, feet.
  add(sph(0.108), [0, 0.895, 0.01]);
  add(cap(0.050, 0.07), [0, 0.775, 0]);
  add(cap(0.150, 0.30), [0, 0.44, 0], null, null, [1, 1, 0.72]);
  add(cap(0.138, 0.09), [0, 0.045, 0], null, null, [1, 1, 0.78]);
  add(cap(0.048, 0.21), [ 0.345, 0.10, 0.025], null, [0, 0, -0.05]);
  add(cap(0.048, 0.21), [-0.345, 0.10, 0.025], null, [0, 0,  0.05]);
  add(sph(0.052), [ 0.362, -0.08, 0.03]);
  add(sph(0.052), [-0.362, -0.08, 0.03]);
  add(sph(0.055), [ 0.122, -0.94, 0.035], null, null, [1, 0.75, 1.5]);
  add(sph(0.055), [-0.122, -0.94, 0.035], null, null, [1, 0.75, 1.5]);
  add(cap(0.085, 0.16), [ 0.118, -0.55, 0], null, null, [1, 1, 0.85]);  // knees
  add(cap(0.085, 0.16), [-0.118, -0.55, 0], null, null, [1, 1, 0.85]);

  // Traps
  add(cap(0.052, 0.11), [ 0.098, 0.700, -0.030], 'traps', [0, 0, -0.60]);
  add(cap(0.052, 0.11), [-0.098, 0.700, -0.030], 'traps', [0, 0,  0.60]);

  // Lats — the V-taper, only fully visible once you turn the figure
  add(cap(0.070, 0.24), [ 0.150, 0.43, -0.070], 'lats', [0, 0, -0.22], [1, 1, 0.70]);
  add(cap(0.070, 0.24), [-0.150, 0.43, -0.070], 'lats', [0, 0,  0.22], [1, 1, 0.70]);

  // Chest — two separated pads, not one bar across the ribcage
  add(sph(0.088), [ 0.072, 0.550, 0.070], 'chest', [0, 0, 0], [0.90, 0.70, 0.62]);
  add(sph(0.088), [-0.072, 0.550, 0.070], 'chest', [0, 0, 0], [0.90, 0.70, 0.62]);

  // Shoulders
  add(sph(0.100), [ 0.258, 0.590, 0], 'shoulders');
  add(sph(0.100), [-0.258, 0.590, 0], 'shoulders');

  // Biceps (front) / triceps (back) — the reason the figure needs to turn
  add(cap(0.054, 0.17), [ 0.300, 0.375, 0.038], 'biceps', [0, 0, -0.08]);
  add(cap(0.054, 0.17), [-0.300, 0.375, 0.038], 'biceps', [0, 0,  0.08]);
  add(cap(0.052, 0.17), [ 0.315, 0.375, -0.048], 'triceps', [0, 0, -0.08]);
  add(cap(0.052, 0.17), [-0.315, 0.375, -0.048], 'triceps', [0, 0,  0.08]);

  // Abs + obliques
  add(cap(0.080, 0.20), [0, 0.255, 0.075], 'abs', null, [1, 1, 0.55]);
  add(cap(0.046, 0.17), [ 0.118, 0.245, 0.045], 'obliques');
  add(cap(0.046, 0.17), [-0.118, 0.245, 0.045], 'obliques');

  // Glutes / quads / hamstrings / calves
  add(sph(0.098), [ 0.095, -0.045, -0.075], 'glutes');
  add(sph(0.098), [-0.095, -0.045, -0.075], 'glutes');
  add(cap(0.082, 0.28), [ 0.114, -0.315, 0.030], 'quads', [0, 0,  0.015]);
  add(cap(0.082, 0.28), [-0.114, -0.315, 0.030], 'quads', [0, 0, -0.015]);
  add(cap(0.066, 0.26), [ 0.118, -0.325, -0.062], 'hamstrings');
  add(cap(0.066, 0.26), [-0.118, -0.325, -0.062], 'hamstrings');
  add(cap(0.064, 0.24), [ 0.120, -0.735, -0.020], 'calves');
  add(cap(0.064, 0.24), [-0.120, -0.735, -0.020], 'calves');

  /* ---- soft contact shadow: grounds the figure, costs one plane ---- */
  (() => {
    const c = document.createElement('canvas');
    c.width = c.height = 128;
    const g = c.getContext('2d');
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, 'rgba(0,0,0,0.55)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
    const plane = new THREE.Mesh(
      new THREE.PlaneGeometry(1.25, 1.25),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false })
    );
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = -1.00;
    scene.add(plane);
  })();

  /* ---- interaction ------------------------------------------------------ */
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  let dragging = false, lastX = 0, lastY = 0, moved = 0;
  let spinVel = 0, idle = 0, activeRegion = null, activeGroups = new Set();
  let targetTiltX = 0;

  const AUTO_SPEED = reduced ? 0 : 0.0022;

  const readyCount = () => Object.values(MUSCLE_STATE).filter((s) => s === 'ready').length;
  const total = Object.keys(MUSCLE_STATE).length;

  function groupToRegion(group) {
    for (const [region, groups] of Object.entries(REGIONS)) if (groups.includes(group)) return region;
    return null;
  }

  container.addEventListener('pointerdown', (e) => {
    dragging = true; moved = 0; lastX = e.clientX; lastY = e.clientY; idle = 0;
    container.classList.add('is-dragging');
    container.setPointerCapture?.(e.pointerId);
  });

  container.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX, dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    moved += Math.abs(dx) + Math.abs(dy);
    figure.rotation.y += dx * 0.008;
    targetTiltX = Math.max(-0.32, Math.min(0.32, targetTiltX + dy * 0.004));
    spinVel = dx * 0.0015;
  });

  function endDrag(e) {
    if (!dragging) return;
    dragging = false;
    container.classList.remove('is-dragging');
    container.releasePointerCapture?.(e.pointerId);
    if (moved < 6) pick(e);   // a tap, not a drag
  }
  container.addEventListener('pointerup', endDrag);
  container.addEventListener('pointercancel', endDrag);
  container.addEventListener('pointerleave', () => {
    if (dragging) { dragging = false; container.classList.remove('is-dragging'); }
  });

  function pick(e) {
    const r = container.getBoundingClientRect();
    ndc.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    ndc.y = -((e.clientY - r.top) / r.height) * 2 + 1;
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObjects(figure.children, false)[0];
    const group = hit?.object?.userData?.group;
    if (!group) return setActive(null);
    // Report the precise muscle, but light up its whole region.
    setActive(groupToRegion(group), NAMES[group], MUSCLE_STATE[group]);
  }

  /**
   * @param {string|null} region  one of REGIONS, or null to clear
   * @param {string} [preciseName]  specific muscle name when picked in 3D
   * @param {string} [preciseState]
   */
  function setActive(region, preciseName, preciseState) {
    activeRegion = region;
    activeGroups = new Set(region ? REGIONS[region] : []);

    if (!onPick) return;
    if (!region) {
      onPick(null, `${readyCount()} of ${total} muscle groups ready to train`);
      return;
    }
    const groups = REGIONS[region];
    const worked = groups.filter((g) => MUSCLE_STATE[g] === 'worked');
    const name = preciseName || REGION_NAMES[region];
    const state = preciseState || (worked.length ? 'worked' : 'ready');
    const text = state === 'worked'
      ? `${name} — still recovering, give it a day`
      : `${name} — fresh, good to train today`;
    onPick(region, text);
  }

  /* ---- render loop ------------------------------------------------------ */
  let running = false, raf = 0, t = 0;

  function frame() {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    t += 0.016;

    if (!dragging) {
      idle += 0.016;
      spinVel *= 0.94;
      figure.rotation.y += spinVel + (idle > 1.6 ? AUTO_SPEED : 0);
      targetTiltX *= 0.97;
    }
    figure.rotation.x += (targetTiltX - figure.rotation.x) * 0.12;

    // Ready muscles breathe; worked muscles sit still and hot.
    if (!reduced) {
      if (materials.ready)  materials.ready.emissiveIntensity  = 0.30 + Math.sin(t * 1.6) * 0.11;
      if (materials.worked) materials.worked.emissiveIntensity = 0.44;
    }

    // Selected region swells slightly.
    for (const [g, meshes] of Object.entries(groupMeshes)) {
      const target = activeGroups.has(g) ? 1.10 : 1;
      for (const m of meshes) {
        const b = m.userData.baseScale;
        m.scale.x += (b.x * target - m.scale.x) * 0.15;
        m.scale.y += (b.y * target - m.scale.y) * 0.15;
        m.scale.z += (b.z * target - m.scale.z) * 0.15;
      }
    }

    renderer.render(scene, camera);
  }

  function start() { if (!running) { running = true; idle = 2; frame(); } }
  function stop()  { running = false; cancelAnimationFrame(raf); }

  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }
  new ResizeObserver(resize).observe(container);

  // Only burn frames while the section is actually on screen.
  new IntersectionObserver(
    (es) => { es.some((e) => e.isIntersecting) ? start() : stop(); },
    { threshold: 0.05 }
  ).observe(container);

  document.addEventListener('visibilitychange', () => { document.hidden ? stop() : start(); });

  setActive(null);
  return { setActive, start, stop };
}
