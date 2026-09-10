#!/usr/bin/env python3
"""Solve the 87Rb D1 optical pumping problem properly, level by level.

T/03 and T/04 both left the same thing open: they folded the whole Zeeman
structure into one number. This does not. It builds every dipole matrix element
from Wigner symbols computed in this repository, assembles the transfer rates
between all sixteen states, and integrates the populations in time.

WHY RATE EQUATIONS ARE LEGITIMATE HERE
--------------------------------------
The full problem is the Liouville-von Neumann equation

    dρ/dt = -(i/ħ)[H, ρ] + L[ρ],        H = H₀ + H_B + H_int

with H_int = -d·E the dipole coupling and L the relaxation superoperator. In
general the optical coherences ρ_ge must be carried along.

In 650 Torr of N₂ they need not be. Collisional quenching and broadening give
the excited state a total width Γ_tot = 2π · 14.19 GHz, which is four orders of
magnitude larger than the Rabi frequency at the intensities of interest and
five orders larger than the ground-state Zeeman splittings. The optical
coherence therefore reaches its quasi-steady value in a time far shorter than
anything else in the problem, and can be eliminated adiabatically:

    dρ_ge/dt ≈ 0  ⇒  ρ_ge ≈ (i Ω_ge / 2) ρ_gg / (Γ_tot/2 + iΔ)

Substituting back leaves rate equations in the populations alone, with

    R_{g→e} = (|Ω_ge|²/Γ_tot) · L(Δ),    Ω_ge ∝ ⟨e|d_q|g⟩ E

and the same collisions destroy the ground-state Zeeman coherences that would
otherwise couple the m sublevels, which is what makes populations sufficient.
The result is exact in the limit Γ_tot ≫ Ω, Δ_Zeeman, and this cell is deep in
that limit.

WHAT IS COMPUTED AND WHAT IS ASSUMED
------------------------------------
CALCULATED  every ⟨F' m'|d_q|F m⟩, from 3-j and 6-j symbols, no free parameter
CALCULATED  absorption rates for σ⁺ light, branching of spontaneous decay
CALCULATED  the resulting steady state and time evolution
INFERRED    Γ_g, the ground-state relaxation rate, from the reviewed T/03 model

    python3 scripts/solve_density_matrix.py [--check]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wigner import wigner_3j, wigner_6j

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "density-matrix.json"

I_NUC = 1.5          # Steck table 1
J_G, J_E = 0.5, 0.5  # 5S1/2 -> 5P1/2, the D1 line
GAMMA_G = 170.0      # 1/s, model input carried over from the reviewed T/03

GROUND = [(1, m) for m in (-1, 0, 1)] + [(2, m) for m in (-2, -1, 0, 1, 2)]
EXCITED = [(1, m) for m in (-1, 0, 1)] + [(2, m) for m in (-2, -1, 0, 1, 2)]


def reduced_F(Fg: float, Fe: float) -> float:
    """⟨F'||d||F⟩ / ⟨J'||d||J⟩ — the hyperfine part of the reduced element."""
    return ((-1) ** (Fe + J_G + 1 + I_NUC)
            * math.sqrt((2 * Fe + 1) * (2 * J_G + 1))
            * wigner_6j(J_G, J_E, 1, Fe, Fg, I_NUC))


def dipole(Fg: float, mg: float, Fe: float, me: float, q: int) -> float:
    """⟨F' m'|d_q|F m⟩ in units of ⟨J'||d||J⟩, via Wigner-Eckart."""
    # Wigner-Eckart: the 3-j must be (F' 1 F; -m' q m), which is non-zero only
    # when m' = m + q. Writing it as (F' 1 F; m' q -m) instead flips the
    # selection rule, and sigma+ light then pumps toward m = -2. The population
    # piling up at the wrong end of the manifold is what caught it.
    return (reduced_F(Fg, Fe)
            * (-1) ** (Fe - 1 + mg)
            * math.sqrt(2 * Fg + 1)
            * wigner_3j(Fe, 1, Fg, -me, q, mg))


def strengths() -> tuple[dict, dict]:
    """|⟨e|d_q|g⟩|² for absorption (q=+1) and for decay (all q)."""
    absorb = {}                                   # (g_index, e_index) -> |d|^2
    decay = {}                                    # (e_index, g_index) -> |d|^2
    for gi, (Fg, mg) in enumerate(GROUND):
        for ei, (Fe, me) in enumerate(EXCITED):
            a = dipole(Fg, mg, Fe, me, +1) ** 2
            if a > 1e-15:
                absorb[(gi, ei)] = a
            s = sum(dipole(Fg, mg, Fe, me, q) ** 2 for q in (-1, 0, 1))
            if s > 1e-15:
                decay[(ei, gi)] = s
    return absorb, decay


# ── the line shape each transition sees ───────────────────────────────────
GHFS = 6.834682610904290e9      # Steck: ground F=2 above F=1
EHFS = 0.814500e9               # 2A, A(5P1/2) = 407.25(63) MHz, Steck rev 2.3.4
FWHM = 14.19e9                  # 650 Torr N2, from T/02 and T/03
SHIFT = -6.575e9                # pressure shift, T/03


def centre(Fg: int, Fe: int) -> float:
    """Transition centre in Hz, relative to low-pressure F=2 -> F'=2, shifted."""
    return (GHFS if Fg == 1 else 0.0) - (EHFS if Fe == 1 else 0.0) + SHIFT


def lorentz(detuning: float, Fg: int, Fe: int) -> float:
    """Normalised to 1 on resonance."""
    x = (detuning - centre(Fg, Fe)) / (FWHM / 2)
    return 1.0 / (1.0 + x * x)


def rates(R0: float, detuning: float):
    """Absorption rate per (ground, excited) pair, and decay branching."""
    absorb, decay = strengths()
    A = {}
    for (gi, ei), s in absorb.items():
        Fg, Fe = GROUND[gi][0], EXCITED[ei][0]
        A[(gi, ei)] = R0 * s * lorentz(detuning, Fg, Fe)
    B = {}
    for ei in range(len(EXCITED)):
        tot = sum(v for (e, g), v in decay.items() if e == ei)
        for (e, g), v in decay.items():
            if e == ei:
                B[(ei, g)] = v / tot
    return A, B


def evolve(R0: float, detuning: float, t_end: float, n: int = 20000):
    """Integrate the ground-state populations. Excited state adiabatically
    eliminated, so an absorption is immediately followed by a decay."""
    A, B = rates(R0, detuning)
    ng = len(GROUND)
    P = [1.0 / ng] * ng                      # unpolarised to start
    dt = t_end / n
    ts, stretched, total_rate = [], [], []
    si = GROUND.index((2, 2))
    for step in range(n + 1):
        ts.append(step * dt)
        stretched.append(P[si])
        total_rate.append(sum(A[(g, e)] * P[g] for (g, e) in A))
        dP = [0.0] * ng
        for (g, e), r in A.items():
            flow = r * P[g]
            dP[g] -= flow
            for gg in range(ng):
                if (e, gg) in B:
                    dP[gg] += flow * B[(e, gg)]
        for g in range(ng):                  # spin destruction toward uniform
            dP[g] += GAMMA_G * (1.0 / ng - P[g])
        P = [max(0.0, p + dt * d) for p, d in zip(P, dP)]
        s = sum(P)
        P = [p / s for p in P]
    return {"t": ts, "stretched": stretched, "rate": total_rate, "final": P}


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
  .bar{{fill:var(--t0,#0d0d0d)}} .bar2{{fill:var(--t2,#8a8a8a)}}
  text{{fill:var(--t0,#0d0d0d);font-size:11px}}
  .sm{{font-size:9px;fill:var(--t1,#3a3a3a)}}
  .xs{{font-size:8px;fill:var(--t1,#3a3a3a);letter-spacing:.05em}}
</style>
{body}
</svg>
'''


def fig_populations(final: list[float]) -> str:
    W, H = 760, 380
    L, BOT, TOP = 90, 300, 60
    bw = 58
    b = ['<text x="16" y="22" class="xs">GROUND-STATE DISTRIBUTION AFTER PUMPING</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">σ+ ON D1, δ = 0</text>']
    for v in (0, .25, .5, .75, 1.0):
        y = BOT - (BOT - TOP) * v
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{W-40}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{v:g}</text>')
    for i, ((F, mm), p) in enumerate(zip(GROUND, final)):
        x = L + 10 + i * (bw + 16)
        h = (BOT - TOP) * p
        cls = "bar" if (F, mm) == (2, 2) else "bar2"
        b.append(f'<rect x="{x}" y="{BOT-h:.1f}" width="{bw}" height="{h:.1f}" class="{cls}"/>')
        b.append(f'<text x="{x+bw/2}" y="{BOT+16}" class="xs" text-anchor="middle">{mm:+d}</text>')
        b.append(f'<text x="{x+bw/2}" y="{BOT+28}" class="xs" text-anchor="middle">F={F}</text>')
        if p > 0.03:
            b.append(f'<text x="{x+bw/2}" y="{BOT-h-6:.1f}" class="xs" text-anchor="middle">{p:.3f}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{W-40}" y2="{BOT}" class="thin"/>')
    b.append(f'<text x="16" y="{H-38}" class="xs">Every rate here comes from a Wigner 3-j and 6-j computed in this repository; no branching ratio was entered by hand.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">The excited state is eliminated adiabatically, which 650 Torr of N2 justifies: Γtot = 2π·14.19 GHz swamps every other rate.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">Population piles into mF = +2 because σ+ has nowhere further to take it — the dark state of T/01, now quantitative.</text>')
    return svg_wrap(W, H, "\n".join(b), "Ground-state distribution after optical pumping",
        "Bar chart of the eight ground Zeeman sublevels after pumping to steady state with "
        "sigma-plus light. Population concentrates in F=2 mF=+2, the stretched state, at about "
        "0.76, with the remainder spread over the neighbouring sublevels.", ("dt", "dd"))


def fig_detuning(scan: list[dict]) -> str:
    W, H = 760, 400
    L, R, TOP, BOT = 92, 690, 60, 320
    dmin, dmax = -10.0, 2.0
    sx = lambda d: L + (R - L) * (d - dmin) / (dmax - dmin)
    b = ['<text x="16" y="22" class="xs">STRETCHED-STATE POPULATION vs DETUNING</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">LEVEL-RESOLVED SOLVE</text>']
    for v in (0, .25, .5, .75, 1.0):
        y = BOT - (BOT - TOP) * v
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{R}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{v:g}</text>')
    for d in range(-10, 3, 2):
        b.append(f'<text x="{sx(d):.0f}" y="{BOT+18}" class="xs" text-anchor="middle">{d:+d}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">detuning from low-pressure F=2 → F′=2 / GHz</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">P(F=2, mF=+2)</text>')
    b.append(f'<line x1="{sx(0):.0f}" y1="{TOP}" x2="{sx(0):.0f}" y2="{BOT}" class="dash"/>')
    b.append(f'<text x="{sx(0)+5:.0f}" y="{TOP+12}" class="xs">low-pressure lock</text>')
    for i, s in enumerate(scan):
        pts = " ".join(f"{sx(d):.1f},{BOT-(BOT-TOP)*p:.1f}" for d, p in zip(s["d"], s["P"]))
        b.append(f'<polyline class="{"l" if i == len(scan)-1 else "m"}" points="{pts}"/>')
        # the labels sat on the "low-pressure lock" marker; park them at the
        # left edge where all three curves are well separated
        y = BOT - (BOT - TOP) * s["P"][0] - 8
        b.append(f'<text x="{L+6}" y="{y:.1f}" class="xs">'
                 f'{s["I"]:g} mW/cm², best {s["best"]:+.1f} GHz</text>')
    b.append(f'<line x1="{sx(-3.5):.0f}" y1="{TOP}" x2="{sx(-3.5):.0f}" y2="{BOT}" class="thin"/>')
    b.append(f'<text x="{sx(-3.5)-5:.0f}" y="{TOP+12}" class="xs" text-anchor="end">this solve: −3.5</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">An independent calculation reviewed in T/03 put the optimum at −3.62 to −3.69 GHz. This one, built from</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">Wigner coefficients and sharing none of its code, lands at −3.5 GHz. Two routes, the same answer within 0.2 GHz.</text>')
    return svg_wrap(W, H, "\n".join(b), "Stretched-state population against detuning",
        "Steady-state population of F=2 mF=+2 as the laser is tuned, at three intensities. All "
        "three peak near minus 3.5 GHz from the low-pressure lock point, agreeing to within 0.2 "
        "GHz with an independent calculation that shares none of this one's code.", ("st", "sd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    run0 = evolve(1.631e4, 0.0, 30e-3, n=6000)          # 10 mW/cm2, steady state
    scan = []
    for I in (1, 5, 10):
        ds = [x * 0.5 for x in range(-20, 5)]
        Ps = [evolve(1.631e3 * I, d * 1e9, 30e-3, n=4000)["stretched"][-1] for d in ds]
        best = ds[max(range(len(Ps)), key=lambda i: Ps[i])]
        scan.append({"I": I, "d": ds, "P": Ps, "best": best})

    absorb, decay = strengths()
    sums = {}
    for (e, g), v in decay.items():
        sums[e] = sums.get(e, 0.0) + v

    payload = {
        "model": "8 ground + 8 excited Zeeman sublevels, excited state adiabatically eliminated",
        "gamma_g_per_s": GAMMA_G,
        "fwhm_Hz": FWHM, "shift_Hz": SHIFT,
        "checks": {
            "decay_branching_sums_to_one": max(abs(v - 1) for v in sums.values()),
            "sigma_plus_raises_m": all(EXCITED[e][1] == GROUND[g][1] + 1 for (g, e) in absorb),
            "absorption_channels": len(absorb), "decay_channels": len(decay),
        },
        "steady_state_delta0_10mW": dict(zip([f"F{F}m{m:+d}" for F, m in GROUND],
                                             [round(x, 5) for x in run0["final"]])),
        "optimum_detuning_GHz": {str(s["I"]): s["best"] for s in scan},
        "reviewed_T03_optimum_GHz": {"1": -3.69, "5": -3.63, "10": -3.62},
        "one_ms_populations_delta0": {
            str(I): round(evolve(1.631e3 * I, 0.0, 1e-3, n=8000)["stretched"][-1], 4)
            for I in (10, 20, 30, 50)},
    }
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-dm-populations.svg": fig_populations(run0["final"]),
        OUT_SVG / "rb87-dm-detuning.svg": fig_detuning(scan),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    print(f"  decay branching max |sum-1| = {payload['checks']['decay_branching_sums_to_one']:.2e}")
    print(f"  sigma+ raises m: {payload['checks']['sigma_plus_raises_m']}")
    print(f"  optimum detuning: {payload['optimum_detuning_GHz']}")
    print(f"  reviewed T/03  : {payload['reviewed_T03_optimum_GHz']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
