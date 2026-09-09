/* RESONANCE — the hidden mode, reached with the Konami code.
 *
 * The thing being played is the thing the site is about: an atom precesses at
 * a rate set by the field it sits in, and a magnetometer works by finding the
 * frequency where the two agree. You tune the field until the trace locks.
 *
 * Four tones, one canvas, no assets. Everything is drawn on a whole-pixel grid
 * and the frame is deliberately coarse, because a smooth one would not belong.
 */
(() => {
  'use strict';
  const KEY = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown',
               'ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
  let seq = [];

  addEventListener('keydown', (e) => {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    seq.push(k);
    if (seq.length > KEY.length) seq.shift();
    if (seq.length === KEY.length && seq.every((v, i) => v === KEY[i])) {
      seq = [];
      start();
    }
  });

  const tone = (n) => getComputedStyle(document.documentElement)
    .getPropertyValue('--t' + n).trim() || ['#0d0d0d','#3a3a3a','#8a8a8a','#d7d7d7'][n];

  let open = false;
  function start() {
    if (open) return;
    open = true;

    const W = 160, H = 144, S = Math.min(4, Math.floor(innerWidth / 200)) || 3;
    const box = document.createElement('div');
    box.className = 'game';
    box.innerHTML =
      '<div class="game-in" role="dialog" aria-modal="true" aria-label="RESONANCE">' +
      '<canvas width="' + W * S + '" height="' + H * S + '"></canvas>' +
      '<p class="game-help">&lt; &gt; TUNE / ESC EXIT</p></div>';
    document.body.appendChild(box);

    const cv = box.querySelector('canvas');
    const g = cv.getContext('2d');
    g.imageSmoothingEnabled = false;
    g.setTransform(S, 0, 0, S, 0, 0);

    // --- state -------------------------------------------------------------
    let field = 50;             // what the player controls
    let target = rand();        // where resonance actually is
    let tol = 9;                // how close counts as locked
    let lock = 0, score = 0, t = 0, alive = true, best = 0;
    try { best = +(localStorage.getItem('shp-res') || 0); } catch (e) { /* blocked */ }

    function rand() { return 14 + Math.floor(Math.random() * 72); }

    const held = new Set();
    const down = (e) => {
      if (e.key === 'Escape') { stop(); return; }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { held.add(e.key); e.preventDefault(); }
      e.stopPropagation();                    // keep the page's pad out of it
    };
    const up = (e) => held.delete(e.key);
    addEventListener('keydown', down, true);
    addEventListener('keyup', up, true);

    function stop() {
      alive = false;
      removeEventListener('keydown', down, true);
      removeEventListener('keyup', up, true);
      box.remove();
      open = false;
    }
    box.addEventListener('click', (e) => { if (e.target === box) stop(); });

    // --- loop --------------------------------------------------------------
    let acc = 0, prev = performance.now();
    (function frame(now) {
      if (!alive) return;
      requestAnimationFrame(frame);
      acc += now - prev; prev = now;
      if (acc < 66) return;                    // ~15 fps, on purpose
      acc = 0; t++;

      if (held.has('ArrowLeft')) field = Math.max(6, field - 1.4);
      if (held.has('ArrowRight')) field = Math.min(94, field + 1.4);

      const off = Math.abs(field - target);
      if (off < tol) {
        lock = Math.min(30, lock + 1);
        if (lock === 30) {
          score++; tol = Math.max(3, tol - 0.7); target = rand(); lock = 0;
          if (score > best) { best = score;
            try { localStorage.setItem('shp-res', String(best)); } catch (e) { /* blocked */ } }
        }
      } else {
        lock = Math.max(0, lock - 1);
      }

      // ---- draw ----
      g.fillStyle = tone(3); g.fillRect(0, 0, W, H);

      // the trace: its frequency is the field, its cleanliness is the lock
      g.fillStyle = tone(0);
      const freq = field / 9, amp = 20 + lock * 0.5;
      for (let x = 0; x < W; x++) {
        const noise = (1 - lock / 30) * (Math.random() - 0.5) * 12;
        const y = 62 + Math.sin((x + t * 3) / (W / freq) * Math.PI * 2) * amp * 0.5 + noise;
        g.fillRect(x, Math.round(y), 1, 2);
      }

      // resonance window, drawn as a bracket rather than a line
      g.fillStyle = tone(2);
      const tx = Math.round(target * (W - 20) / 100) + 10;
      const tw = Math.max(3, Math.round(tol * (W - 20) / 100));
      g.fillRect(tx - tw, 112, tw * 2, 2);
      g.fillRect(tx - tw, 108, 2, 6); g.fillRect(tx + tw - 2, 108, 2, 6);

      // the player's needle
      g.fillStyle = tone(0);
      const fx = Math.round(field * (W - 20) / 100) + 10;
      g.fillRect(fx - 1, 104, 3, 14);

      // lock meter, in whole blocks
      for (let i = 0; i < 10; i++) {
        g.fillStyle = i < Math.floor(lock / 3) ? tone(0) : tone(2);
        g.fillRect(8 + i * 6, 128, 4, 4);
      }

      // score, drawn as blocks so no font is needed
      g.fillStyle = tone(0);
      for (let i = 0; i < Math.min(score, 12); i++) g.fillRect(W - 10 - i * 6, 8, 4, 4);
      g.fillStyle = tone(2);
      for (let i = 0; i < Math.min(best, 12); i++) g.fillRect(W - 10 - i * 6, 16, 4, 2);

      g.strokeStyle = tone(0); g.lineWidth = 2;
      g.strokeRect(1, 1, W - 2, H - 2);
    })(prev);
  }
})();
