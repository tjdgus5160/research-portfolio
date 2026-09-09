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


  /* ── power on ───────────────────────────────────────────────────────────
     Plays once per browser session, the way a handheld boots when you switch
     it on rather than every time you change screens. The page underneath is
     already rendered; this only covers it, so nothing depends on it finishing. */
  const boot = document.getElementById('boot');
  const root = document.documentElement;
  if (boot) {
    let seen = false;
    try { seen = sessionStorage.getItem('shp-boot') === '1'; } catch (e) { /* blocked */ }
    if (seen || still) {
      boot.remove();
    } else {
      const line = boot.querySelector('.boot-line');
      if (line) line.textContent = 'SHP®  OK';
      const live = document.querySelector('.boot-live');
      if (live) live.textContent = '시작 화면';
      root.classList.add('booting');
      boot.hidden = false;
      const done = () => {
        root.classList.remove('booting');
        boot.remove();
        try { sessionStorage.setItem('shp-boot', '1'); } catch (e) { /* blocked */ }
      };
      // driven by the wipe finishing, with a wall-clock backstop so a dropped
      // animationend can never leave the page covered
      const wipe = boot.querySelector('.boot-wipe');
      setTimeout(() => snd.thunk(), 2150);
      const t = setTimeout(done, 3200);
      if (wipe) wipe.addEventListener('animationend', () => { clearTimeout(t); done(); },
                                      { once: true });
      // let anyone skip it
      addEventListener('keydown', function esc(e) {
        if (e.key !== 'Escape' && e.key !== 'Enter' && e.key !== ' ') return;
        clearTimeout(t); done(); removeEventListener('keydown', esc);
      });
      boot.addEventListener('click', () => { clearTimeout(t); done(); });
    }
  }

  /* ── how far down the page we are, in whole blocks ────────────────────── */
  const fill = document.querySelector('.prog i');
  if (fill) {
    let queued = false;
    const paint = () => {
      queued = false;
      const max = document.documentElement.scrollHeight - innerHeight;
      const pct = max > 0 ? (scrollY / max) * 100 : 0;
      // snap to 2% so the meter advances in steps, never smoothly
      fill.style.setProperty('--sp', (Math.round(pct / 2) * 2) + '%');
    };
    addEventListener('scroll', () => {
      if (!queued) { queued = true; requestAnimationFrame(paint); }
    }, { passive: true });
    addEventListener('resize', paint, { passive: true });
    paint();
  }

  /* ── things arrive in hard stops as they enter ────────────────────────── */
  const steps = ['r1', 'r2', 'r3'];
  // .sr-only headings are 1px tall, so they can never satisfy the observer's
  // threshold and would sit at opacity 0 for ever — visually identical, but it
  // is still an element hidden from assistive tech by an animation that never
  // runs. They are excluded rather than special-cased later.
  document.querySelectorAll('.slab > *, .hero-copy, .screen, .work article, .svc li')
    .forEach((el) => { if (!el.classList.contains('sr-only')) el.setAttribute('data-r', ''); });

  if (still) {
    document.querySelectorAll('[data-r]').forEach((el) => el.classList.add('r3'));
    document.querySelectorAll('.svc li').forEach((el) => el.classList.add('on'));
    document.querySelector('.screen')?.classList.add('lit');
  } else {
    const stagger = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const el = e.target;
        steps.forEach((c, i) => setTimeout(() => el.classList.add(c), i * 90));
        if (el.matches('.svc li')) {
          setTimeout(() => el.classList.add('on'), 160);
          setTimeout(() => snd.tick(), 200);
        }
        if (el.matches('.screen')) setTimeout(() => el.classList.add('lit'), 120);
        if (el.matches('.manifesto')) el.classList.add('on');
        stagger.unobserve(el);
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -6% 0px' });
    document.querySelectorAll('[data-r], .manifesto').forEach((el) => stagger.observe(el));
  }

  /* ── each service row carries its index in binary ─────────────────────── */
  document.querySelectorAll('.svc li .no').forEach((no, i) => {
    no.dataset.bits = (i + 1).toString(2).padStart(4, '0');
  });


  /* ── sound ──────────────────────────────────────────────────────────────
     Synthesised, not sampled: the DMG made its noise with two square-wave
     pulse channels and a noise channel, so square oscillators and a filtered
     noise burst are the honest way to reproduce it — and it ships nothing.

     Browsers refuse to start audio before a gesture, which is the whole reason
     the boot is silent on a cold load. The context is created on the first
     click or key, the chime plays at that moment, and the choice is remembered
     so a returning visitor is not surprised twice. */
  const snd = (() => {
    let ctx = null, master = null;
    let on = false, unlocked = false;
    try { on = localStorage.getItem('shp-snd') !== '0'; } catch (e) { on = true; }

    const btn = document.querySelector('.snd');
    const paint = () => btn && btn.setAttribute('aria-pressed', String(on && unlocked));

    const build = () => {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return false;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 0.09;             // quiet enough to live with
      master.connect(ctx.destination);
      return true;
    };

    /* one square-wave note with a hard on/off envelope, so it reads as a chip
       tone rather than a synth pad */
    const note = (freq, at, dur, level = 1, type = 'square') => {
      if (!ctx) return;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = type;
      o.frequency.setValueAtTime(freq, at);
      g.gain.setValueAtTime(0, at);
      g.gain.linearRampToValueAtTime(level, at + 0.004);   // avoid a click
      g.gain.setValueAtTime(level, at + dur - 0.02);
      g.gain.linearRampToValueAtTime(0, at + dur);
      o.connect(g); g.connect(master);
      o.start(at); o.stop(at + dur + 0.02);
    };

    /* the noise channel: short filtered burst, used for the boot wipe */
    const noise = (at, dur, level = 0.5) => {
      if (!ctx) return;
      const n = Math.floor(ctx.sampleRate * dur);
      const buf = ctx.createBuffer(1, n, ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
      const src = ctx.createBufferSource(); src.buffer = buf;
      const f = ctx.createBiquadFilter(); f.type = 'bandpass';
      f.frequency.value = 1400; f.Q.value = 0.7;
      const g = ctx.createGain(); g.gain.value = level;
      src.connect(f); f.connect(g); g.connect(master);
      src.start(at);
    };

    const can = () => on && unlocked && ctx && ctx.state === 'running';

    const api = {
      /* power-on: a rising arpeggio landing on a held fifth */
      chime() {
        if (!can()) return;
        const t = ctx.currentTime + 0.02;
        [523.25, 659.25, 783.99].forEach((f, i) => note(f, t + i * 0.085, 0.08, 0.85));
        note(1046.5, t + 0.30, 0.34, 0.7);
        note(783.99, t + 0.30, 0.34, 0.4);
        noise(t + 0.30, 0.09, 0.22);
      },
      blip(f = 880) { if (can()) note(f, ctx.currentTime + 0.01, 0.045, 0.8); },
      tick()        { if (can()) note(1318.5, ctx.currentTime + 0.01, 0.022, 0.34); },
      thunk()       { if (can()) noise(ctx.currentTime + 0.01, 0.13, 0.45); },
      get on() { return on && unlocked; },
    };

    /* The first gesture unlocks it, whatever that gesture is. This listener is
       on the capture phase, so when the gesture *is* the sound button it runs
       before the button's own handler — which would then immediately toggle
       back off what this just turned on. Note which case it was and let the
       button skip that one press. */
    let viaButton = false;
    const unlock = (e) => {
      if (unlocked) return;
      if (!ctx && !build()) return;
      unlocked = true;
      viaButton = !!(e && e.target && e.target.closest && e.target.closest('.snd'));
      ctx.resume?.();
      paint();
      if (on) api.chime();                  // they hear the boot sound here
      ['pointerdown', 'keydown', 'touchstart'].forEach(
        (t) => removeEventListener(t, unlock, true));
    };
    ['pointerdown', 'keydown', 'touchstart'].forEach(
      (t) => addEventListener(t, unlock, true));

    if (btn) {
      btn.addEventListener('click', () => {
        if (!unlocked) { unlock(); return; }
        if (viaButton) { viaButton = false; return; }  // that press did the unlocking
        on = !on;
        try { localStorage.setItem('shp-snd', on ? '1' : '0'); } catch (e) { /* blocked */ }
        paint();
        if (on) api.blip(1046.5);
      });
    }
    paint();
    return api;
  })();

  /* every control answers back */
  document.querySelectorAll('a.btn, .bar-nav a, .menu a, .chan a').forEach((el) => {
    el.addEventListener('pointerenter', () => snd.tick());
    el.addEventListener('click', () => snd.blip(el.matches('.btn') ? 660 : 880));
  });

  /* ── palette switch, kept per viewer ────────────────────────────────── */
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
