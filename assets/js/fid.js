/* fid.js — the hero motif.
 *
 * A free induction decay: after the pump is cut, the atomic spins precess at
 * the Larmor frequency and dephase. That is the signal this whole field is
 * built on, so it is the right thing to have moving on the page.
 *
 * It is COMPUTED from the parameters below, not measured. The page says so
 * next to it. A picture of a signal is not a signal.
 *
 *     s(t) = A · exp(-t / T2) · cos(2π f_L t + φ)
 *     f_L  = (γ/2π) · B0
 *
 * The numbers are a shielded-cell case, chosen so the shape reads at this
 * size: ~10 cycles across the window with the decay clearly visible.
 */

export const FID = {
  isotope: "87Rb",
  gamma: 6.995779,     // γ/2π, Hz/nT  (⁸⁷Rb ground-state)
  B0_uT: 1.0,          // bias field, µT
  T2_ms: 1.0,          // transverse relaxation time
  window_ms: 1.5,      // time axis shown
  phase: 0,
};

FID.fL_Hz = FID.gamma * FID.B0_uT * 1000;   // µT → nT

export function label() {
  const kHz = (FID.fL_Hz / 1000).toFixed(3);
  return `${FID.isotope} · γ/2π ${FID.gamma} Hz/nT · B₀ ${FID.B0_uT.toFixed(2)} µT`
       + ` · f_L ${kHz} kHz · T₂ ${FID.T2_ms.toFixed(1)} ms`;
}

/** s(t) for t in milliseconds, normalised to ±1. */
function signal(t_ms) {
  const env = Math.exp(-t_ms / FID.T2_ms);
  const ph = 2 * Math.PI * (FID.fL_Hz / 1000) * t_ms + FID.phase;
  return env * Math.cos(ph);
}

function css(el, name) {
  return getComputedStyle(el).getPropertyValue(name).trim();
}

export function mountFID(canvas) {
  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  let w = 0, h = 0, dpr = 1;
  let sweep = reduced ? 1 : 0;
  let raf = null;
  let started = 0;

  const colors = () => ({
    trace: css(canvas, "--accent") || "#E63950",
    env: css(canvas, "--accent-dim") || "#8E1F30",
    axis: css(canvas, "--line") || "#2A2325",
  });

  function resize() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    const r = canvas.getBoundingClientRect();
    w = Math.max(1, Math.floor(r.width));
    h = Math.max(1, Math.floor(r.height));
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function draw() {
    const c = colors();
    const mid = h / 2;
    const amp = h * 0.26;
    const n = Math.max(2, Math.floor(w));

    ctx.clearRect(0, 0, w, h);

    // zero line — an oscilloscope has one, so this does
    ctx.strokeStyle = c.axis;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, Math.round(mid) + 0.5);
    ctx.lineTo(w, Math.round(mid) + 0.5);
    ctx.stroke();

    // decay envelope ±A·exp(-t/T2), the thing the trace is bounded by
    ctx.strokeStyle = c.env;
    ctx.lineWidth = 1;
    for (const sign of [1, -1]) {
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const x = (i / n) * w;
        const t = (i / n) * FID.window_ms;
        const y = mid - sign * amp * Math.exp(-t / FID.T2_ms);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      }
      ctx.stroke();
    }

    // the trace, swept in
    const upto = Math.floor(n * sweep);
    ctx.strokeStyle = c.trace;
    ctx.globalAlpha = 0.55;
    ctx.lineWidth = 1.25;
    ctx.lineJoin = "round";
    ctx.shadowColor = c.trace;
    ctx.shadowBlur = 6;
    ctx.beginPath();
    for (let i = 0; i <= upto; i++) {
      const x = (i / n) * w;
      const t = (i / n) * FID.window_ms;
      const y = mid - amp * signal(t);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;

    // the sweep head, while it is still running
    if (sweep < 1 && upto > 0) {
      const x = (upto / n) * w;
      const t = (upto / n) * FID.window_ms;
      const y = mid - amp * signal(t);
      ctx.fillStyle = c.trace;
      ctx.beginPath();
      ctx.arc(x, y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function frame(ts) {
    if (!started) started = ts;
    sweep = Math.min(1, (ts - started) / 1600);
    draw();
    if (sweep < 1) raf = requestAnimationFrame(frame);
    else raf = null;
  }

  const ro = new ResizeObserver(resize);
  ro.observe(canvas);
  resize();
  if (!reduced) raf = requestAnimationFrame(frame);

  return {
    destroy() {
      ro.disconnect();
      if (raf) cancelAnimationFrame(raf);
    },
  };
}
