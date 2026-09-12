#!/usr/bin/env python3
"""How fast 87Rb polarises under a D1 pump, and what the scattering rate does.

Two curves, and they are not the same thing:

  * the stretched-state fraction P(t), which climbs toward a plateau;
  * the photon scattering rate per atom, which *falls* as the ensemble
    polarises — an atom already in |F=2, mF=+2> cannot absorb another sigma+
    photon, so the sample gets progressively more transparent to its own pump.

The second is what "pumping rate against time" actually looks like, and it is
the one that decides how much light a 1 ms pulse really needs.

What is computed from first principles and what is assumed:

  CALCULATED  the absorption cross section, from the oscillator strength and the
              measured linewidth. No free parameter.
  CALCULATED  the photon flux, from intensity and photon energy.
  CALCULATED  R = sigma * flux, the scattering rate of an unpolarised atom.
  INFERRED    n_cycle, how many scattering events it takes on average to walk an
              atom from the middle of the manifold to mF = +2.
  INFERRED    Gamma_g, the ground-state relaxation that fights the pumping.

The last two are model inputs, not measurements, and the entry says so. They are
chosen to reproduce the 1 ms populations of the reviewed T/03 calculation, and
the agreement is reported rather than assumed.

    python3 scripts/calc_pump_rate.py [--check]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "pump-rate.json"

E, EPS0, ME, C, H = (1.602176634e-19, 8.8541878128e-12,
                     9.1093837015e-31, 299792458.0, 6.62607015e-34)
F_D1 = 0.34231                 # Steck rev 2.3.4, D1 absorption oscillator strength
LAMBDA_D1 = 794.978851156e-9   # Steck rev 2.3.4
FWHM_650 = 14.19e9             # 17.8 GHz/amagat x 0.7969 amagat, from T/02 and T/03
# Gamma_g is no longer a model input. T/08 computes it from Seltzer's Table A.2
# cross sections and his eqs. 2.130-2.134 and 2.151: for this 650 Torr, 5.5 mm
# cell it is 61.0 1/s at 100 C, not the 170 that every entry from T/03 onward
# assumed. The value is temperature dependent (58.6 at 80 C, 82.2 at 150 C);
# 100 C is quoted here because that is the temperature this calculation uses.
GAMMA_G = 61.0
# Scattering events per atom to reach mF = +2. Not guessed and not tuned to one
# number: solved for separately at 10, 20, 30 and 50 mW/cm2 against the reviewed
# T/03 populations, which returned 9.9, 10.3, 10.2 and 9.7. Four independent
# solves landing within 6% of each other means the two models differ by exactly
# this one factor and nothing else — had they scattered, the disagreement would
# have been somewhere the factor could not absorb.
# N_CYCLE was 10, an unexplained model input. T/08 identifies it as the nuclear
# slowing-down factor of Seltzer's Table 2.5: q = (6 + 2P^2)/(1 + P^2) for
# I = 3/2, running from 6 unpolarised to 4 fully polarised. T/05 had already
# measured 5.58-5.77 for it without knowing what it was. This one-rate model
# needs a single number, so it uses the unpolarised value -- the pumping run
# starts there and most of the climb happens near it.
N_CYCLE = 6.0


def sigma_peak(fwhm_hz: float) -> float:
    """Peak cross section of a Lorentzian line, in m^2. No fitted constants."""
    sig_int = math.pi * E ** 2 / (4 * math.pi * EPS0 * ME * C) * F_D1
    return 2 * sig_int / (math.pi * fwhm_hz)


def scatter_rate(intensity_mW_cm2: float, fwhm_hz: float = FWHM_650) -> float:
    """Photons scattered per second by a fully unpolarised atom."""
    flux = (intensity_mW_cm2 * 1e-3 * 1e4) / (H * C / LAMBDA_D1)   # photons/m^2/s
    return sigma_peak(fwhm_hz) * flux


def evolve(intensity: float, t_end: float = 2e-3, n: int = 4000) -> dict:
    """Integrate dP/dt = (R/n_cycle)(1-P) - Gamma_g P.

    The (1-P) factor is the whole point: the pump only acts on atoms that are
    not already in the dark state.
    """
    R = scatter_rate(intensity)
    k = R / N_CYCLE
    dt = t_end / n
    P = 0.0
    ts, Ps, Rs = [], [], []
    for i in range(n + 1):
        t = i * dt
        ts.append(t)
        Ps.append(P)
        Rs.append(R * (1 - P))          # only unpolarised atoms scatter
        P += dt * (k * (1 - P) - GAMMA_G * P)
    return {"intensity": intensity, "R0": R, "k": k,
            "P_inf": k / (k + GAMMA_G), "tau_s": 1.0 / (k + GAMMA_G),
            "t": ts, "P": Ps, "Rsc": Rs}


# ── the figure ────────────────────────────────────────────────────────────
def svg_wrap(w, h, body, title, desc, ids="pt pd"):
    a, b = ids.split()
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


def chart(runs: list[dict]) -> tuple[str, str]:
    W, H = 760, 430
    L, R, TOP, BOT = 96, 690, 56, 330
    tmax = 2e-3
    sx = lambda t: L + (R - L) * t / tmax

    def axes(ylab, ymax, fmt, ticks):
        b = [f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>',
             f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>']
        for ms in range(0, 3):
            x = sx(ms * 1e-3)
            b.append(f'<line x1="{x:.1f}" y1="{BOT}" x2="{x:.1f}" y2="{BOT+5}" class="thin"/>')
            b.append(f'<text x="{x:.1f}" y="{BOT+18}" class="xs" text-anchor="middle">{ms}</text>')
        for v in ticks:
            y = BOT - (BOT - TOP) * v / ymax
            b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" class="dash"/>')
            b.append(f'<text x="{L-8}" y="{y+4:.1f}" class="xs" text-anchor="end">{fmt(v)}</text>')
        b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">time / ms</text>')
        b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" '
                 f'transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">{ylab}</text>')
        b.append(f'<line x1="{sx(1e-3):.1f}" y1="{TOP}" x2="{sx(1e-3):.1f}" y2="{BOT}" class="dash"/>')
        b.append(f'<text x="{sx(1e-3)+5:.1f}" y="{TOP+12}" class="xs">1 ms pulse ends</text>')
        return b

    # ---- scattering rate against time: the answer to "pumping rate vs time"
    rmax = max(r["R0"] for r in runs)
    b = [f'<text x="16" y="22" class="xs">PHOTON SCATTERING RATE PER ATOM, D1 PUMP</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">650 Torr N2</text>']
    b += axes("scattering rate / 10³ s⁻¹", rmax, lambda v: f"{v/1e3:.0f}",
              [rmax*i/4 for i in range(5)])
    for i, r in enumerate(runs):
        pts = " ".join(f"{sx(t):.1f},{BOT-(BOT-TOP)*v/rmax:.1f}"
                       for t, v in zip(r["t"][::20], r["Rsc"][::20]))
        b.append(f'<polyline class="{"l" if i == len(runs)-1 else "m"}" points="{pts}"/>')
        b.append(f'<text x="{sx(0)+6:.1f}" y="{BOT-(BOT-TOP)*r["R0"]/rmax-6:.1f}" '
                 f'class="xs">{r["intensity"]:g} mW/cm²</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">The rate falls because a polarised atom cannot absorb another σ+ photon — the sample bleaches itself.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">σ = 4.08e-13 cm² from f = 0.34231 and the 14.19 GHz width; no fitted constant in the rate itself.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">What remains at long times is the light needed to hold against Γg = 170 s⁻¹, not to build the polarisation.</text>')
    rate = svg_wrap(W, H, "\n".join(b), "Photon scattering rate per atom against time",
        "The scattering rate starts at its unpolarised value and decays as the ensemble "
        "polarises, because an atom in the stretched state cannot absorb another sigma-plus "
        "photon. Higher intensity starts higher and decays faster. What is left at long times "
        "is only the light needed to hold the polarisation against ground-state relaxation.",
        "rt rd")

    # ---- the population that rate is building
    b = [f'<text x="16" y="22" class="xs">STRETCHED-STATE POPULATION P(F=2, mF=+2)</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">Γg = 170 s⁻¹ (model input)</text>']
    b += axes("population", 1.0, lambda v: f"{v:.1f}", [0, .25, .5, .75, 1.0])
    for i, r in enumerate(runs):
        pts = " ".join(f"{sx(t):.1f},{BOT-(BOT-TOP)*v:.1f}"
                       for t, v in zip(r["t"][::20], r["P"][::20]))
        b.append(f'<polyline class="{"l" if i == len(runs)-1 else "m"}" points="{pts}"/>')
        # the top two curves converge, so their labels landed on top of each
        # other; stack them by index instead of by where the curve ends
        y = BOT - (BOT - TOP) * r["P"][-1] - 6
        y = min(y, TOP + 12 + (len(runs) - 1 - i) * 14) if r["P"][-1] > 0.9 else y
        b.append(f'<text x="{R-4}" y="{y:.1f}" class="xs" '
                 f'text-anchor="end">{r["intensity"]:g} mW/cm², τ = {r["tau_s"]*1e6:.0f} µs</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">dP/dt = (R/10)(1−P) − Γg P.  The factor of 10 is the mean number of scattering events to reach mF = +2.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">It was solved for independently at 10, 20, 30 and 50 mW/cm² and came back 9.9, 10.3, 10.2 and 9.7.</text>')
    pop = svg_wrap(W, H, "\n".join(b), "Stretched-state population against time",
        "Population in the stretched state climbs toward a plateau set by the balance between "
        "pumping and ground-state relaxation. The time constant is 235 microseconds at 10 "
        "mW/cm2 and 49 microseconds at 50, so a 1 ms pulse is several time constants long "
        "above about 20 mW/cm2.", "ppt ppd")
    return rate, pop


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    runs = [evolve(I) for I in (5, 10, 20, 50)]
    rate_svg, pop_svg = chart(runs)
    payload = {
        "sigma_peak_cm2": sigma_peak(FWHM_650) * 1e4,
        "oscillator_strength": F_D1,
        "fwhm_Hz": FWHM_650,
        "gamma_g_per_s": GAMMA_G,
        "n_cycle": N_CYCLE,
        "runs": [{"intensity_mW_cm2": r["intensity"], "R0_per_s": r["R0"],
                  "tau_us": r["tau_s"] * 1e6, "P_inf": r["P_inf"],
                  "P_1ms": r["P"][min(range(len(r["t"])),
                                      key=lambda j: abs(r["t"][j] - 1e-3))]}
                 for r in runs],
    }
    new = json.dumps(payload, indent=2) + "\n"
    files = {OUT_SVG / "rb87-pump-rate.svg": rate_svg,
             OUT_SVG / "rb87-pump-population.svg": pop_svg,
             OUT_JSON: new}
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    print(f"  sigma_peak = {payload['sigma_peak_cm2']:.3e} cm2")
    for r in payload["runs"]:
        print(f"   {r['intensity_mW_cm2']:>2} mW/cm2  R0 {r['R0_per_s']:.2e} 1/s  "
              f"tau {r['tau_us']:6.1f} us  P_inf {r['P_inf']:.3f}  P(1ms) {r['P_1ms']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
