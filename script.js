/* SHP® — 8-bit interface behaviour. Everything here is drawn on a whole-pixel
   grid; nothing animates smoothly, because the point is that it cannot. */
(() => {
  'use strict';
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── the mobile menu ────────────────────────────────────────────────── */
  const burger = document.querySelector('.burger');
  const menu = document.getElementById('menu');
  if (burger && menu) {
    const set = (open) => {
      menu.hidden = !open;
      burger.setAttribute('aria-expanded', String(open));
    };
    burger.addEventListener('click', () => set(menu.hidden));
    menu.addEventListener('click', (e) => { if (e.target.matches('a')) set(false); });
    addEventListener('keydown', (e) => { if (e.key === 'Escape') set(false); });
  }

  /* ── the ticker, filled with the binary the page is asked to be made of ── */
  const run = document.querySelector('.ticker-run');
  if (run) {
    const words = ['794.98', '780.24', 'SOURCE_FACT', 'CALCULATED', 'INFERRED',
                   'ILLUSTRATIVE', 'MEASURED NOT ASSUMED', 'SHP®'];
    const bits = (n) => Array.from({ length: n },
      () => (Math.random() < 0.5 ? '0' : '1')).join('');
    let line = '';
    for (const w of words) line += `${bits(8)} ▪ ${w} ▪ `;
    // duplicated so the -50% slide loops without a seam
    run.textContent = (line + line).replace(/\s+$/, '');
  }

  /* ── the footer's bit field ─────────────────────────────────────────── */
  const bits = document.querySelector('.bits');
  if (bits) {
    bits.textContent = Array.from({ length: 240 },
      () => (Math.random() < 0.5 ? '0' : '1')).join('');
  }

  /* ── falling binary, snapped to a character cell so it stays 8-bit ──── */
  const cv = document.querySelector('.rain');
  if (cv && !still) {
    const ctx = cv.getContext('2d', { alpha: true });
    const CELL = 16;              // one glyph cell, in CSS pixels
    let cols = 0, drops = [], raf = 0, last = 0;

    const size = () => {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      cv.width = Math.ceil(innerWidth * dpr);
      cv.height = Math.ceil(innerHeight * dpr);
      cv.style.width = innerWidth + 'px';
      cv.style.height = innerHeight + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.font = `${CELL - 4}px "Press Start 2P", monospace`;
      ctx.textBaseline = 'top';
      cols = Math.ceil(innerWidth / CELL);
      drops = Array.from({ length: cols },
        () => Math.floor(Math.random() * (innerHeight / CELL)));
    };

    const ink = () => getComputedStyle(document.documentElement)
      .getPropertyValue('--t1').trim() || '#3a3a3a';

    const tick = (t) => {
      raf = requestAnimationFrame(tick);
      if (t - last < 90) return;          // deliberately choppy, ~11 fps
      last = t;
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      ctx.fillStyle = ink();
      const rows = Math.ceil(innerHeight / CELL);
      for (let i = 0; i < cols; i++) {
        const y = drops[i];
        for (let k = 0; k < 5; k++) {          // a short trail per column
          const r = y - k;
          if (r < 0 || r > rows) continue;
          ctx.globalAlpha = 1 - k * 0.19;
          ctx.fillText(Math.random() < 0.5 ? '0' : '1', i * CELL, r * CELL);
        }
        ctx.globalAlpha = 1;
        drops[i] = y > rows + Math.random() * 18 ? 0 : y + 1;
      }
    };

    size();
    addEventListener('resize', size, { passive: true });
    raf = requestAnimationFrame(tick);
    addEventListener('pagehide', () => cancelAnimationFrame(raf));
  }

  /* ── palette switch, kept per viewer ────────────────────────────────── */
  const root = document.documentElement;
  try {
    const saved = localStorage.getItem('shp-pal');
    if (saved === 'dmg' || saved === 'mono') root.dataset.pal = saved;
  } catch (e) { /* private window, or site data blocked */ }
  addEventListener('keydown', (e) => {
    if (e.key !== 'p' && e.key !== 'P') return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    const next = root.dataset.pal === 'dmg' ? 'mono' : 'dmg';
    root.dataset.pal = next;
    try { localStorage.setItem('shp-pal', next); } catch (err) { /* ignore */ }
  });
})();
