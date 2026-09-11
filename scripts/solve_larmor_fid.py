#!/usr/bin/env python3
"""What the magnetometer actually measures: precession, and how it dies.

Everything from T/01 to T/06 is about getting the atoms polarised. This is the
other half. Turn the pump off, tip the spins onto the equator, and they precess
around the field at the Larmor frequency until they dephase. That precession,
read out as Faraday rotation by the probe of W/02, is the signal.

Two things make the answer more than one number:

  The Zeeman sublevels are not evenly spaced. To first order they are, and the
  four Delta-m = 1 coherences in F=2 all precess at g_F mu_B B / h. The
  Breit-Rabi formula says otherwise at second order, and the splitting it puts
  between adjacent transitions is exactly a quarter of the clock shift Steck
  tabulates -- which is how this file checks itself.

  The tipped state is not a perfect spin-coherent state. T/05 leaves 5.5% of
  the population outside m = +2, and that asymmetry weights the four lines
  unevenly. A symmetric weighting has its centroid exactly on the linear Larmor
  frequency; an asymmetric one does not, and the residue is a systematic error
  that no amount of averaging removes.

    python3 scripts/solve_larmor_fid.py [--check]
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wigner import wigner_d

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "larmor-fid.json"

# ── constants, all from Steck rev 2.3.4 ───────────────────────────────────
MU_B_HZ_G = 1.39962449361e6      # Table 1: mu_B = h * 1.399 624 493 61(42) MHz/G
A_HFS_HZ = 3.417341305452145e9   # Table 5: A(5^2S_1/2) = h * 3.417 341 305 452 145 GHz
I_NUC = 1.5                      # Table 2
J_G = 0.5
G_J = 2.002331070                # Table 6: g_J(5^2S_1/2) = 2.002 331 070(26)
G_I = -0.0009951414              # Table 6: nuclear g-factor
DE_HFS_HZ = A_HFS_HZ * (I_NUC + 0.5)      # Steck below eq. 26: DE_hfs = A(I + 1/2)
CLOCK_SHIFT_HZ_G2 = 575.15       # Table 6, quoted as 2*pi * 575.15 Hz/G^2

GAMMA_G = 170.0                  # 1/s, the same model input carried from T/03


def g_F(F: float) -> float:
    """Steck eq. 23, with the nuclear term kept (it is a 0.1% correction)."""
    a = (F * (F + 1) - I_NUC * (I_NUC + 1) + J_G * (J_G + 1)) / (2 * F * (F + 1))
    b = (F * (F + 1) + I_NUC * (I_NUC + 1) - J_G * (J_G + 1)) / (2 * F * (F + 1))
    return G_J * a + G_I * b


def breit_rabi(F: float, mF: float, B_gauss: float) -> float:
    """Steck eq. 26, in Hz. F = 2 is the upper branch, F = 1 the lower."""
    x = (G_J - G_I) * MU_B_HZ_G * B_gauss / DE_HFS_HZ
    sign = 1.0 if F > I_NUC else -1.0
    root = math.sqrt(1.0 + 4.0 * mF * x / (2 * I_NUC + 1) + x * x)
    return (-DE_HFS_HZ / (2 * (2 * I_NUC + 1)) + G_I * MU_B_HZ_G * mF * B_gauss
            + sign * DE_HFS_HZ / 2 * root)


def stretched_exact(mF: float, B_gauss: float) -> float:
    """Steck eq. 28, valid only at m = +/-(I + 1/2). Used here as a check."""
    return (DE_HFS_HZ * I_NUC / (2 * I_NUC + 1)
            + math.copysign(0.5, mF) * (G_J + 2 * I_NUC * G_I) * MU_B_HZ_G * B_gauss)


def transitions(F: int) -> tuple[tuple[int, int], ...]:
    ms = list(range(F, -F - 1, -1))
    return tuple(zip(ms[:-1], ms[1:]))


def zeeman_lines(B_gauss: float, F: int = 2) -> list[float]:
    """The Delta-m = 1 precession frequencies inside one F manifold, in Hz.

    Reported as magnitudes. F = 1 has g_F < 0 and precesses the other way; what
    a magnitude readout sees is |g_F| mu_B B / h either way.
    """
    return [abs(breit_rabi(F, hi, B_gauss) - breit_rabi(F, lo, B_gauss))
            for hi, lo in transitions(F)]


def tipped_coherences(pops: dict[int, float], beta: float = math.pi / 2,
                      F: int = 2) -> list[float]:
    """Rotate a diagonal state by beta about y, then read <F_+>.

    rho' = D rho D^dagger, so rho'_{a,b} = sum_m d_{a,m} d_{b,m} rho_{m,m}, and
    the transverse magnetisation collects the m, m-1 elements weighted by
    <m|F_+|m-1> = sqrt(F(F+1) - m(m-1)).

    At beta = pi/2 exactly, and only there, d^j_{-m',m}(pi/2) =
    (-1)^(j+m) d^j_{m',m}(pi/2). The sign depends on the summation index and
    not on m', so it squares away inside the product above and the weight of
    the (m, m-1) coherence equals that of (-m+1, -m) whatever the populations
    were. That symmetry is what puts the centroid of the four lines exactly on
    the linear Larmor frequency -- and what a tip error destroys.
    """
    ff = F * (F + 1)
    return [math.sqrt(ff - hi * (hi - 1))
            * sum(wigner_d(F, hi, m, beta) * wigner_d(F, lo, m, beta) * p
                  for m, p in pops.items())
            for hi, lo in transitions(F)]


def centroid(pops: dict[int, float], B_gauss: float, beta: float = math.pi / 2,
             F: int = 2) -> float:
    w = tipped_coherences(pops, beta, F)
    return sum(wi * fi for wi, fi in zip(w, zeeman_lines(B_gauss, F))) / sum(w)


def field_error_nT(pops: dict[int, float], B_gauss: float, beta: float,
                   F: int = 2) -> float:
    """How far off the field reads, if the centroid is taken as g_F mu_B B / h."""
    slope = abs(g_F(F)) * MU_B_HZ_G                   # Hz per gauss
    return (centroid(pops, B_gauss, beta, F)
            - slope * B_gauss) / slope * 1e5          # gauss -> nT


def fid(B_gauss: float, pops: dict[int, float], t2: float, t_end: float,
        beta: float = math.pi / 2, n: int = 1200) -> dict:
    """The precession signal, demodulated at the linear Larmor frequency.

    The carrier is 350 kHz and the structure worth seeing is 36 Hz wide, so the
    raw waveform is unplottable: four thousand cycles under one envelope. What
    is drawn instead is the in-phase quadrature after mixing down at
    g_F mu_B B / h, which is what a lock-in or a digital demodulator produces
    and what a frequency fit actually works on.
    """
    f = zeeman_lines(B_gauss)
    w = tipped_coherences(pops, beta)
    f0 = abs(g_F(2)) * MU_B_HZ_G * B_gauss
    ts = [t_end * k / n for k in range(n + 1)]
    demod, dephase = [], []
    for t in ts:
        c = sum(wi * math.cos(2 * math.pi * (fi - f0) * t) for wi, fi in zip(w, f))
        dephase.append(c)
        demod.append(c * math.exp(-t / t2))
    return {"t": ts, "demod": demod, "dephase": dephase, "f": f, "w": w,
            "f0": f0, "total": sum(w)}


def spectrum(B_gauss: float, pops: dict[int, float], t2: float,
             half_width_hz: float, n: int = 900) -> dict:
    """Each coherence is a Lorentzian of FWHM 1/(pi T2), centred on its own line."""
    f0 = abs(g_F(2)) * MU_B_HZ_G * B_gauss
    fw = 1.0 / (math.pi * t2)
    out = []
    for F in (2, 1):
        w = tipped_coherences(pops[F], math.pi / 2, F)
        out.append((zeeman_lines(B_gauss, F), w))
    xs = [-half_width_hz + 2 * half_width_hz * k / n for k in range(n + 1)]
    ys = []
    for x in xs:
        v = 0.0
        for lines, ws in out:
            for fi, wi in zip(lines, ws):
                v += wi / (1 + ((x + f0 - fi) / (fw / 2)) ** 2)
        ys.append(v)
    return {"x": xs, "y": ys, "fwhm": fw, "f0": f0,
            "lines": [(l, w) for l, w in out]}


# ── figures ───────────────────────────────────────────────────────────────
def svg_wrap(w, h, body, title, desc, ids):
    a, b = ids
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
  role="img" aria-labelledby="{a} {b}" class="lvl">
<title id="{a}">{title}</title><desc id="{b}">{desc}</desc>
<style>
  .lvl{{font-family:"IBM Plex Mono","SF Mono",monospace}}
  .l{{stroke:var(--t0,#0d0d0d);stroke-width:3;fill:none}}
  .m{{stroke:var(--t1,#3a3a3a);stroke-width:2;fill:none}}
  .thin{{stroke:var(--t1,#3a3a3a);stroke-width:1.5;fill:none}}
  .dash{{stroke:var(--t2,#8a8a8a);stroke-width:1;stroke-dasharray:3 4;fill:none}}
  text{{fill:var(--t0,#0d0d0d);font-size:11px}}
  .sm{{font-size:9px;fill:var(--t1,#3a3a3a)}}
  .xs{{font-size:8px;fill:var(--t1,#3a3a3a);letter-spacing:.05em}}
  /* A label that lands on a gridline or a curve is unreadable. Paint the
     ground colour behind the glyphs first, then the glyphs. */
  .xs,.sm{{paint-order:stroke fill;stroke:var(--t3,#d7d7d7);stroke-width:3px;
    stroke-linejoin:round}}
</style>
{body}
</svg>
'''


def _frame(b, L, R, TOP, BOT, ys, xs, ylab, xlab, fmt_y=str, fmt_x=str):
    for v, y in ys:
        b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.1f}" class="xs" text-anchor="end">{fmt_y(v)}</text>')
    for v, x in xs:
        b.append(f'<text x="{x:.1f}" y="{BOT+18}" class="xs" text-anchor="middle">{fmt_x(v)}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">{xlab}</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" '
             f'transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">{ylab}</text>')


def fig_fan(bmax: float = 1.0, n: int = 120) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 96, 640, 62, 320
    span = 240.0                                     # Hz, full scale each way
    sx = lambda B: L + (R - L) * B / bmax
    sy = lambda v: (TOP + BOT) / 2 - (BOT - TOP) / 2 * v / span
    b = ['<text x="16" y="22" class="xs">THE FOUR F=2 TRANSITIONS ARE NOT DEGENERATE</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">LINEAR LARMOR SUBTRACTED</text>']
    _frame(b, L, R, TOP, BOT,
           [(v, sy(v)) for v in (-200, -100, 0, 100, 200)],
           [(x / 5, sx(x / 5)) for x in range(6)],
           "frequency − g_F μ_B B / h  /  Hz", "field / gauss",
           lambda v: f"{v:+g}", lambda v: f"{v:g}")
    slope = abs(g_F(2)) * MU_B_HZ_G
    labels = []
    for i, (hi, lo) in enumerate(transitions(2)):
        pts, last = [], 0.0
        for k in range(n + 1):
            B = bmax * k / n
            v = (breit_rabi(2, hi, B) - breit_rabi(2, lo, B)) - slope * B
            last = v
            pts.append(f"{sx(B):.1f},{sy(v):.1f}")
        b.append(f'<polyline class="{"l" if i in (0, 3) else "m"}" points="{" ".join(pts)}"/>')
        labels.append(f'<text x="{R+6}" y="{sy(last)+3:.1f}" class="xs">'
                      f'm {hi:+d} → {lo:+d}</text>')
    b += labels
    b.append(f'<text x="{L+8}" y="{sy(170):.1f}" class="xs">'
             f'to first order all four lie on zero</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">Adjacent transitions separate by 143.79 Hz/G² — exactly a quarter of the clock shift Steck tabulates as 575.15 Hz/G².</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">That relation is not put in. It falls out of diagonalising the Breit-Rabi formula, and it is how this calculation checks itself.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">At Earth\'s field, 0.5 G, the outer two sit ±54 Hz from the centre. The linewidth at Γ_g = 170 s⁻¹ is 54 Hz.</text>')
    return svg_wrap(W, H, "\n".join(b), "Second-order Zeeman splitting of the F=2 transitions",
        "Four curves showing how the Delta-m = 1 transition frequencies inside F=2 separate "
        "quadratically with magnetic field once the linear Larmor term is removed, reaching "
        "about 215 hertz at one gauss.", ("fnt", "fnd"))


def fig_fid(run_t2: dict, run_inf: dict, t2: float) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 96, 660, 62, 320
    t_end = run_t2["t"][-1]
    amp = run_inf["total"]
    sx = lambda t: L + (R - L) * t / t_end
    sy = lambda v: (TOP + BOT) / 2 - (BOT - TOP) / 2 * v / amp
    b = ['<text x="16" y="22" class="xs">FREE INDUCTION DECAY, DEMODULATED AT THE LINEAR LARMOR FREQUENCY</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">0.5 G, π/2 TIP</text>']
    _frame(b, L, R, TOP, BOT,
           [(v, sy(v * amp)) for v in (-1, -0.5, 0, 0.5, 1)],
           [(x * 5, sx(x * 5e-3)) for x in range(5)],
           "in-phase quadrature", "time after the tip / ms",
           lambda v: f"{v:+g}", lambda v: f"{v:g}")
    for key, run, cls in (("dephase", run_inf, "m"), ("demod", run_t2, "l")):
        pts = " ".join(f"{sx(t):.1f},{sy(v):.1f}" for t, v in zip(run["t"], run[key]))
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
    env = " ".join(f"{sx(t):.1f},{sy(amp*math.exp(-t/t2)):.1f}" for t in run_t2["t"])
    b.append(f'<polyline class="dash" points="{env}"/>')
    b.append(f'<text x="{sx(t_end*0.62):.0f}" y="{sy(amp*0.78):.0f}" class="xs">'
             f'dephasing only, no relaxation</text>')
    tl = t_end * 0.42
    b.append(f'<line x1="{sx(tl):.0f}" y1="{sy(amp*math.exp(-tl/t2)):.0f}" '
             f'x2="{sx(tl):.0f}" y2="{sy(-amp*0.32):.0f}" class="dash"/>')
    b.append(f'<text x="{sx(tl)+6:.0f}" y="{sy(-amp*0.35):.0f}" class="xs">'
             f'exp(−t/T₂), T₂ = {t2*1e3:.2f} ms</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">The carrier is 350 kHz. What is drawn is what a demodulator leaves: four tones at −54, −18, +18 and +54 Hz beating against each other.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">The grey curve is the same signal with relaxation switched off. It still dies, and crosses zero at 16 ms — that is the Zeeman splitting alone.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">At this field the two mechanisms are comparable, so a single exponential fit to the envelope reads a T₂ shorter than the real one.</text>')
    return svg_wrap(W, H, "\n".join(b), "Free induction decay",
        "Demodulated precession signal against time, with and without relaxation. The trace "
        "without relaxation still decays and reverses, because the four Zeeman transitions "
        "beat against one another.", ("fdt", "fdd"))


def fig_spectrum(narrow: dict, wide: dict, t2a: float, t2b: float) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 96, 660, 62, 320
    hw = wide["x"][-1]
    sx = lambda f: L + (R - L) * (f + hw) / (2 * hw)
    sy = lambda v: BOT - (BOT - TOP) * v
    b = ['<text x="16" y="22" class="xs">THE LINE, AND WHAT IS INSIDE IT</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">0.5 G, TWO COHERENCE TIMES</text>']
    _frame(b, L, R, TOP, BOT,
           [(v, sy(v)) for v in (0, 0.25, 0.5, 0.75, 1.0)],
           [(x * 50, sx(x * 50)) for x in range(-3, 4)],
           "absorption, arbitrary", "frequency − g_F μ_B B / h  /  Hz",
           lambda v: f"{v:g}", lambda v: f"{v:+g}")
    # Each curve is scaled to its own peak: the question is whether the
    # structure resolves, not how tall the absorption gets.
    for run, cls in ((wide, "m"), (narrow, "l")):
        mx = max(run["y"])
        pts = " ".join(f"{sx(x):.1f},{sy(y/mx):.1f}" for x, y in zip(run["x"], run["y"]))
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
    for fi, wi in zip(*wide["lines"][0]):
        x = sx(fi - wide["f0"])
        b.append(f'<line x1="{x:.1f}" y1="{BOT}" x2="{x:.1f}" y2="{BOT-10-30*wi:.1f}" class="thin"/>')
    for i, (cls, lab) in enumerate((("l", f"T₂ = {t2b*1e3:.0f} ms — four lines"),
                                    ("m", f"T₂ = {t2a*1e3:.2f} ms — one bump"))):
        y = TOP + 12 + 15 * i
        b.append(f'<line x1="{L+8}" y1="{y-3}" x2="{L+30}" y2="{y-3}" class="{cls}"/>')
        b.append(f'<text x="{L+36}" y="{y}" class="xs">{lab}</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">The sticks are the four F=2 transitions, 36 Hz apart at this field, with the weights a π/2 tip gives them.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">At Γ_g = 170 s⁻¹ the Lorentzian width is 54 Hz and they merge into one line that is wider than any of them.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">Nothing here resolves the structure away. It is still in the signal, and it still beats — see the previous figure.</text>')
    return svg_wrap(W, H, "\n".join(b), "The precession line and its structure",
        "Spectrum of the precession signal at two coherence times. With the short one the four "
        "Zeeman transitions merge into a single broadened line; with a long one they resolve "
        "into four separate peaks.", ("spt", "spd"))


def fig_tip(pops: dict, B_gauss: float, degs: list[float]) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 104, 660, 62, 320
    errs = [field_error_nT(pops, B_gauss, math.radians(d)) for d in degs]
    lim = 8.0
    sx = lambda d: L + (R - L) * (d - degs[0]) / (degs[-1] - degs[0])
    sy = lambda v: (TOP + BOT) / 2 - (BOT - TOP) / 2 * v / lim
    b = ['<text x="16" y="22" class="xs">WHAT A TIP-ANGLE ERROR COSTS</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">50 μT, THE FIELD AT THE SURFACE</text>']
    _frame(b, L, R, TOP, BOT,
           [(v, sy(v)) for v in (-8, -4, 0, 4, 8)],
           [(d, sx(d)) for d in (30, 60, 90, 120, 150)],
           "apparent field error / nT", "tip angle / degrees",
           lambda v: f"{v:+g}", lambda v: f"{v:g}°")
    pts = " ".join(f"{sx(d):.1f},{sy(e):.1f}" for d, e in zip(degs, errs))
    b.append(f'<polyline class="l" points="{pts}"/>')
    b.append(f'<line x1="{sx(90):.1f}" y1="{TOP}" x2="{sx(90):.1f}" y2="{BOT}" class="dash"/>')
    b.append(f'<circle cx="{sx(90):.1f}" cy="{sy(0):.1f}" r="3" fill="var(--t0,#0d0d0d)"/>')
    b.append(f'<text x="{sx(90)-6:.0f}" y="{sy(0)+16:.0f}" class="xs" text-anchor="end">'
             f'exactly zero at π/2</text>')
    e95 = field_error_nT(pops, B_gauss, math.radians(95))
    b.append(f'<circle cx="{sx(95):.1f}" cy="{sy(e95):.1f}" r="2.5" fill="var(--t0,#0d0d0d)"/>')
    b.append(f'<text x="{sx(95)+8:.0f}" y="{sy(e95)-8:.0f}" class="xs">'
             f'5° off → {e95:+.2f} nT</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">At exactly π/2 the coherence weights are symmetric whatever the pumping left behind, so the second-order Zeeman cancels out of the centroid.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">Away from π/2 it does not, and the field reads {abs(e95)/5:.3f} nT per degree. Repeating the measurement does not help: the error is in the pulse.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">It scales as B², so the same pulse error costs a hundred times less at 5 μT — and four times more at 1 gauss.</text>')
    return svg_wrap(W, H, "\n".join(b), "Field error against tip angle",
        "Apparent magnetic field error against the tip angle of the pulse, passing through zero "
        "at exactly ninety degrees and rising to about 0.65 nanotesla five degrees away.",
        ("tpt", "tpd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    # The starting distribution is not assumed: it is what T/05 leaves behind.
    dm = json.loads((ROOT / "analysis" / "density-matrix.json").read_text())
    ss = dm["steady_state_delta0_10mW"]
    pops = {2: {m: ss[f"F2m{m:+d}"] for m in (2, 1, 0, -1, -2)},
            1: {m: ss[f"F1m{m:+d}"] for m in (1, 0, -1)}}

    T2 = 1.0 / GAMMA_G                    # INFERRED; see the entry's unknown list
    T2_LONG = 0.06
    B = 0.5                               # gauss, roughly the field at the surface

    slope = abs(g_F(2)) * MU_B_HZ_G
    lines = zeeman_lines(B)
    gaps = [lines[i + 1] - lines[i] for i in range(3)]

    checks = {
        # Steck gives two independent routes to the m = +/-2 energies.
        "eq26_vs_eq28_max_Hz": max(
            abs(breit_rabi(2, m, b) - stretched_exact(m, b))
            for m in (2, -2) for b in (0.1, 0.5, 5.0, 50.0)),
        # and tabulates the clock shift, which the same formula must reproduce
        "clock_shift_Hz_per_G2": ((breit_rabi(2, 0, 1.0) - breit_rabi(1, 0, 1.0))
                                  - (breit_rabi(2, 0, 0.0) - breit_rabi(1, 0, 0.0))),
        "clock_shift_tabulated": CLOCK_SHIFT_HZ_G2,
        # the Zeeman gap is a quarter of it, and that is not put in anywhere
        "zeeman_gap_Hz_per_G2": gaps[1] / B ** 2,
        "quarter_of_clock": CLOCK_SHIFT_HZ_G2 / 4,
        # a pi/2 tip must give symmetric weights for any diagonal state
        "pi2_weight_asymmetry": max(
            abs(w[0] - w[3]) + abs(w[1] - w[2])
            for w in (tipped_coherences(p, math.pi / 2)
                      for p in ({2: 1.0}, pops[2], {2: .5, 1: .3, 0: .15, -1: .05}))),
        # <F_x> after a pi/2 tip must equal <F_z> before it
        "fx_after_equals_fz_before": abs(
            sum(tipped_coherences(pops[2])) - sum(m * p for m, p in pops[2].items())),
    }

    degs = [30 + 0.5 * k for k in range(241)]
    payload = {
        "sources": {
            "g_J": G_J, "g_I": G_I, "mu_B_Hz_per_G": MU_B_HZ_G,
            "A_hfs_S_Hz": A_HFS_HZ, "Delta_E_hfs_Hz": DE_HFS_HZ,
            "note": "Steck rev 2.3.4 Tables 1, 2, 5, 6 and equations 23, 26, 28, 29"},
        "g_F": {"2": g_F(2), "1": g_F(1)},
        "larmor_Hz_per_G": slope,
        "larmor_Hz_per_nT": slope / 1e5,
        "checks": {k: (round(v, 6) if isinstance(v, float) else v)
                   for k, v in checks.items()},
        "at_0p5_G": {
            "linear_Hz": slope * B,
            "F2_lines_Hz": [round(x, 3) for x in lines],
            "F1_lines_Hz": [round(x, 3) for x in zeeman_lines(B, 1)],
            "F2_minus_F1_Hz": round(zeeman_lines(B, 1)[0] - lines[1], 1),
            "adjacent_gap_Hz": round(gaps[1], 4),
            "linewidth_Hz": round(1 / (math.pi * T2), 2),
            "F2_weights": [round(x, 6) for x in tipped_coherences(pops[2])],
            "F1_weights": [round(x, 6) for x in tipped_coherences(pops[1], math.pi / 2, 1)],
            "F1_fraction_of_signal": round(
                sum(tipped_coherences(pops[1], math.pi / 2, 1))
                / sum(tipped_coherences(pops[2])), 6)},
        "T2_s": T2,
        "T2_provenance": ("INFERRED. Gamma_g = 170 1/s is the only relaxation number in "
                          "this repository and it entered T/03 as a longitudinal ground-state "
                          "rate. Using 1/Gamma_g as T2 assumes T1 = T2."),
        "tip_error_nT_at_50uT": {str(d): round(field_error_nT(pops[2], B, math.radians(d)), 5)
                                 for d in (60, 80, 85, 89, 90, 91, 95, 100, 120)},
        "tip_error_slope_nT_per_deg": round(
            field_error_nT(pops[2], B, math.radians(95)) / 5, 5),
        "tip_error_B_scaling": {str(b): round(field_error_nT(pops[2], b, math.radians(95)), 6)
                                for b in (0.05, 0.5, 1.0)},
    }
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-zeeman-fan.svg": fig_fan(),
        OUT_SVG / "rb87-fid.svg": fig_fid(
            fid(B, pops[2], T2, 20e-3), fid(B, pops[2], 1e9, 20e-3), T2),
        OUT_SVG / "rb87-fid-spectrum.svg": fig_spectrum(
            spectrum(B, pops, T2_LONG, 150.0), spectrum(B, pops, T2, 150.0), T2, T2_LONG),
        OUT_SVG / "rb87-tip-error.svg": fig_tip(pops[2], B, degs),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    print(f"  g_F(2) = {g_F(2):.7f}   {slope/1e5:.5f} Hz/nT")
    print(f"  eq.26 vs eq.28          {checks['eq26_vs_eq28_max_Hz']:.2e} Hz")
    print(f"  clock shift             {checks['clock_shift_Hz_per_G2']:.4f} vs "
          f"{CLOCK_SHIFT_HZ_G2} Hz/G2 tabulated")
    print(f"  Zeeman gap              {checks['zeeman_gap_Hz_per_G2']:.4f} vs "
          f"{CLOCK_SHIFT_HZ_G2/4:.4f} Hz/G2 (clock/4)")
    print(f"  pi/2 weight asymmetry   {checks['pi2_weight_asymmetry']:.2e}")
    print(f"  <Fx> after = <Fz> before {checks['fx_after_equals_fz_before']:.2e}")
    print(f"  tip error               {payload['tip_error_slope_nT_per_deg']:.4f} nT/degree "
          f"at 50 uT, scaling as B^2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
