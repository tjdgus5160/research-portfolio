#!/usr/bin/env python3
"""Push the pump through the cell instead of assuming it survives the trip.

Everything up to here assumed the same intensity everywhere in the vapour.
T/03 and T/04 both flagged that as the next thing to fix, because the atoms at
the front absorb first and the ones at the back see whatever is left. The two
effects feed each other: absorption depletes the beam, but a polarised atom
stops absorbing, so a strong beam bleaches a path for itself and a weak one does
not. That coupling is what this solves.

    dI/dz = -n sigma (1 - P(z)) I(z)        Beer-Lambert, but only unpolarised
                                            atoms absorb
    dP/dt = (R(z)/n_cycle)(1 - P) - Gamma_g P

integrated together on a grid through the 5.5 mm path.

Vapour density comes from the model Steck quotes, with its stated accuracy:

    log10 Pv = 2.881 + 4.312 - 4040/T     (liquid phase, torr)
    "specified to have an accuracy better than +/-5% from 298-550 K"

    python3 scripts/solve_cell_propagation.py [--check]
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "cell-propagation.json"

K_B = 1.380649e-23
H, C = 6.62607015e-34, 299792458.0
LAMBDA_D1 = 794.978851156e-9
SIGMA_650 = 4.076e-13 * 1e-4     # m^2, from T/04
# Gamma_g is no longer a model input. T/08 computes it from Seltzer's Table A.2
# cross sections and his eqs. 2.130-2.134 and 2.151: for this 650 Torr, 5.5 mm
# cell it is 61.0 1/s at 100 C, not the 170 that every entry from T/03 onward
# assumed. The value is temperature dependent (58.6 at 80 C, 82.2 at 150 C);
# 100 C is quoted here because that is the temperature this calculation uses.
GAMMA_G = 61.0
# N_CYCLE was 10, an unexplained model input. T/08 identifies it as the nuclear
# slowing-down factor of Seltzer's Table 2.5: q = (6 + 2P^2)/(1 + P^2) for
# I = 3/2, running from 6 unpolarised to 4 fully polarised. T/05 had already
# measured 5.58-5.77 for it without knowing what it was. This one-rate model
# needs a single number, so it uses the unpolarised value -- the pumping run
# starts there and most of the climb happens near it.
N_CYCLE = 6.0
L_CELL = 5.5e-3                  # m, the active path named in T/03
T_MELT = 312.46                  # K, Steck: melting point 39.31 C


def vapour_pressure_torr(T: float) -> float:
    """Steck eq. 1. Solid below the melting point, liquid above."""
    if T < T_MELT:
        return 10 ** (2.881 + 4.857 - 4215.0 / T)
    return 10 ** (2.881 + 4.312 - 4040.0 / T)


def density_m3(T: float) -> float:
    """Total Rb number density. n = P/kT with P converted from torr."""
    return vapour_pressure_torr(T) * 133.322368 / (K_B * T)


ABUNDANCE_NATURAL = 0.2783        # 87Rb fraction in natural rubidium


def density_87(T: float, enrichment: float = ABUNDANCE_NATURAL) -> float:
    """Only 87Rb absorbs the D1 line addressed here.

    Enrichment matters more than it looks. Against natural abundance the
    optical depths in T/03 come out 2.49x larger at every temperature — a
    constant ratio, so a single differing assumption rather than scattered
    error. 0.2783 x 2.49 = 0.693, which is an enriched cell; cells for
    magnetometry are routinely 70% 87Rb or better. Which this cell is has not
    been established here, so both are reported.
    """
    return density_m3(T) * enrichment


# ── the level-resolved absorber, imported rather than re-derived ──────────
# T/05 solves the eight ground sublevels with Wigner coefficients computed in
# this repository. Re-implementing them here would mean two copies to keep
# right, so this loads that module and uses its strengths, line shapes and
# branching directly.
_spec = importlib.util.spec_from_file_location(
    "dm", Path(__file__).resolve().parent / "solve_density_matrix.py")
dm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dm)

PHOTON_E = H * C / LAMBDA_D1
# Rate scale: sigma_0 * flux, expressed per mW/cm^2. Derived, not pasted, so it
# cannot drift away from the cross section the optical depths are built on.
RATE_PER_MW_CM2 = SIGMA_650 * 10.0 / PHOTON_E


def channels(detuning: float):
    """Absorption weights and decay branching at one detuning.

    A[(g,e)] is per unit R0; summed over the channels against an unpolarised
    ground state with every component on resonance it comes to 1, which is what
    makes sigma_0 above and the rates here the same physical statement.
    """
    absorb, decay = dm.strengths()
    A = {(g, e): dm.POL_AVG * v * dm.lorentz(detuning, dm.GROUND[g][0], dm.EXCITED[e][0])
         for (g, e), v in absorb.items()}
    B = {}
    for ei in range(len(dm.EXCITED)):
        tot = sum(v for (e, g), v in decay.items() if e == ei)
        for (e, g), v in decay.items():
            if e == ei:
                B[(ei, g)] = v / tot
    return A, B


def optical_depth(T: float, length: float = L_CELL,
                  enrichment: float = ABUNDANCE_NATURAL,
                  detuning: float | None = None) -> float:
    """Unpolarised vapour. The number that decides whether the back of the cell
    sees any light at all.

    Two conventions, and they differ by more than rounding:

    detuning=None   n sigma_0 L, with sigma_0 the Lorentzian peak built from the
                    whole D1 oscillator strength. This is what T/03 reports, and
                    it answers "what if all the strength sat at this frequency".
    a number        the attenuation the vapour actually presents there, with the
                    strength split across the four hyperfine components. At the
                    low-pressure F=2 lock point it is 0.69 of the first, because
                    the pressure shift has moved the F=2 line 6.6 GHz away.
    """
    od = density_87(T, enrichment) * SIGMA_650 * length
    if detuning is None:
        return od
    A, _ = channels(detuning)
    return od * sum(A.values()) / len(dm.GROUND)


def propagate(I0_mW_cm2: float, T: float, detuning: float = 0.0,
              enrichment: float = ABUNDANCE_NATURAL, t_end: float = 1e-3,
              nz: int = 40, nt: int = 2000,
              snap_at: tuple[float, ...] = ()) -> dict:
    """Integrate the beam and the atoms together through the cell.

    At each time step the beam is pushed from front to back, attenuated by
    whatever the local ground-state distribution actually absorbs; then every
    slab is advanced by the intensity that reached it. Neither can be solved
    first -- that is the whole point.

    The absorber is the eight-sublevel solve from T/05, not a (1 - P) factor.
    That matters here in a way it did not in T/04: a partly pumped slab is not
    a mixture of "polarised" and "unpolarised" atoms with one cross section
    between them, and the population left in F=1 absorbs on a line 6.8 GHz away.
    """
    n87 = density_87(T, enrichment)
    A, B = channels(detuning)
    ng = len(dm.GROUND)
    si = dm.GROUND.index((2, 2))
    dz, dt = L_CELL / nz, t_end / nt
    P = [[1.0 / ng] * ng for _ in range(nz)]
    hist = {k: [] for k in ("t", "front", "back", "mean", "transmission")}
    snaps, want = [], list(snap_at)
    # The very last slab moves with the grid (0.244 at nz=20, 0.225 at nz=80),
    # because the gradient there is steep. The last tenth of the cell does not.
    tail = max(1, nz // 10)
    I_end = I0_mW_cm2
    for step in range(nt + 1):
        I, slab_I = I0_mW_cm2, []
        for k in range(nz):
            a = sum(w * P[k][g] for (g, e), w in A.items())
            alpha = n87 * SIGMA_650 * a                      # 1/m
            I_next = I * math.exp(-alpha * dz)
            # the slab is pumped by its own average intensity, not its front face
            slab_I.append((I - I_next) / (alpha * dz) if alpha * dz > 1e-12 else I)
            I = I_next
        I_end = I
        hist["t"].append(step * dt)
        hist["front"].append(P[0][si])
        hist["back"].append(sum(p[si] for p in P[-tail:]) / tail)
        hist["mean"].append(sum(p[si] for p in P) / nz)
        hist["transmission"].append(I / I0_mW_cm2)
        while want and step * dt >= want[0] - 0.5 * dt:
            snaps.append({"t": want.pop(0), "P": [p[si] for p in P]})
        if step == nt:
            break
        for k in range(nz):
            R0 = RATE_PER_MW_CM2 * slab_I[k]
            pk, dP = P[k], [0.0] * ng
            for (g, e), w in A.items():
                flow = R0 * w * pk[g]
                dP[g] -= flow
                for gg in range(ng):
                    if (e, gg) in B:
                        dP[gg] += flow * B[(e, gg)]
            for g in range(ng):
                dP[g] += GAMMA_G * (1.0 / ng - pk[g])
            q = [max(0.0, x + dt * d) for x, d in zip(pk, dP)]
            tot = sum(q)
            P[k] = [x / tot for x in q]
    return {**hist, "profile": [p[si] for p in P], "snaps": snaps,
            "OD0": n87 * SIGMA_650 * L_CELL, "I_out": I_end}


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


def fig_profile(runs: list[tuple[float, dict]]) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 92, 636, 62, 320
    sx = lambda z: L + (R - L) * z / (L_CELL * 1e3)
    b = ['<text x="16" y="22" class="xs">POLARISATION THROUGH THE CELL AFTER A 1 ms PULSE</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">30 mW/cm² AT THE WINDOW</text>']
    for v in (0, .25, .5, .75, 1.0):
        y = BOT - (BOT - TOP) * v
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{R}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{v:g}</text>')
    for z in (0, 1, 2, 3, 4, 5):
        b.append(f'<text x="{sx(z):.0f}" y="{BOT+18}" class="xs" text-anchor="middle">{z}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">depth into the cell / mm</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">P(F=2, mF=+2)</text>')
    for i, (Tc, r) in enumerate(runs):
        nz = len(r["profile"])
        pts = " ".join(f"{sx(k*L_CELL*1e3/(nz-1)):.1f},{BOT-(BOT-TOP)*p:.1f}"
                       for k, p in enumerate(r["profile"]))
        b.append(f'<polyline class="{"l" if i == len(runs)-1 else "m"}" points="{pts}"/>')
    # 80 and 100 C end within 0.001 of each other, so their labels would print on
    # top of one another. Push each block down until it clears the one above.
    ends = [BOT - (BOT - TOP) * r["profile"][-1] for _, r in runs]
    ys, floor_y = [], TOP + 4
    for y in sorted(ends):
        y = max(y, floor_y)
        ys.append(y)
        floor_y = y + 26
    order = sorted(range(len(runs)), key=lambda i: ends[i])
    for slot, i in enumerate(order):
        Tc, r = runs[i]
        y = ys[slot]
        if abs(y - ends[i]) > 1:            # label moved: draw a leader to its curve
            b.append(f'<line x1="{R}" y1="{ends[i]:.1f}" x2="{R+18}" y2="{y-4:.1f}" class="dash"/>')
        b.append(f'<text x="{R+22}" y="{y:.1f}" class="xs">{Tc:g} °C</text>')
        b.append(f'<text x="{R+22}" y="{y+12:.1f}" class="xs">OD {r["OD0"]:.1f}</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">The front polarises the same way at every temperature. What changes is how far the bleaching front gets in 1 ms.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">80 and 100 °C are not drawn: at OD 0.2 and 0.9 they lie exactly on the 120 °C line.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">Each slab is the eight-sublevel solve of T/05, so the stretched state is genuinely dark and the vapour opens a channel for itself.</text>')
    return svg_wrap(W, H, "\n".join(b), "Polarisation through the cell",
        "Stretched-state population against depth into a 5.5 mm cell after a one millisecond "
        "pump pulse, at four temperatures. Up to an optical depth of about three the profile is "
        "flat; at an optical depth of sixteen it falls away through the second half of the cell.",
        ("pft", "pfd"))


def fig_bleach(run: dict, Tc: float) -> str:
    """The thing a steady-state picture cannot show: the front moving in."""
    W, H = 760, 400
    L, R, TOP, BOT = 92, 636, 62, 320
    sx = lambda z: L + (R - L) * z / (L_CELL * 1e3)
    b = [f'<text x="16" y="22" class="xs">THE BLEACHING FRONT, {Tc:g} °C</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">OD {run["OD0"]:.1f}, 30 mW/cm²</text>']
    for v in (0, .25, .5, .75, 1.0):
        y = BOT - (BOT - TOP) * v
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{R}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{v:g}</text>')
    for z in (0, 1, 2, 3, 4, 5):
        b.append(f'<text x="{sx(z):.0f}" y="{BOT+18}" class="xs" text-anchor="middle">{z}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">depth into the cell / mm</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">P(F=2, mF=+2)</text>')
    for i, sn in enumerate(run["snaps"]):
        nz = len(sn["P"])
        pts = " ".join(f"{sx(k*L_CELL*1e3/(nz-1)):.1f},{BOT-(BOT-TOP)*p:.1f}"
                       for k, p in enumerate(sn["P"]))
        b.append(f'<polyline class="{"l" if i == len(run["snaps"])-1 else "m"}" points="{pts}"/>')
    # Four of the five snapshots leave the back of the cell at the same value,
    # so labelling each one where its own curve ends stacks them in the wrong
    # order. Sort by that value, then push apart and draw a leader to each.
    ends = [(BOT - (BOT - TOP) * sn["P"][-1], sn) for sn in run["snaps"]]
    floor_y = TOP + 4
    for cy, sn in sorted(ends):
        y = max(cy, floor_y)
        floor_y = y + 15
        if abs(y - cy) > 1:
            b.append(f'<line x1="{R}" y1="{cy:.1f}" x2="{R+14}" y2="{y-3:.1f}" class="dash"/>')
        b.append(f'<text x="{R+18}" y="{y+3:.1f}" class="xs">{sn["t"]*1e3:g} ms</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">A thick cell does not polarise all over at once. The front tenth clears first, stops absorbing, and hands the beam to the next tenth.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">At 0.2 ms the back is untouched; by 1 ms the front has swept nine tenths of the way through. Nothing in the model puts it there.</text>')
    return svg_wrap(W, H, "\n".join(b), "The bleaching front",
        "Stretched-state population against depth at five times during a one millisecond pulse "
        f"at {Tc:g} degrees. The polarised region starts at the entrance window and advances "
        "into the cell as each layer stops absorbing.", ("blt", "bld"))


def fig_detuning(scans: list[dict]) -> str:
    """Does the optimum move once the beam is depleted? T/03 asked; this answers."""
    W, H = 760, 414
    L, R, TOP, BOT = 92, 660, 62, 320
    dmin, dmax = -10.0, 2.0
    sx = lambda d: L + (R - L) * (d - dmin) / (dmax - dmin)
    b = ['<text x="16" y="22" class="xs">CELL-MEAN POLARISATION vs DETUNING, WITH PROPAGATION</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">1 ms PULSE</text>']
    for v in (0, .25, .5, .75, 1.0):
        y = BOT - (BOT - TOP) * v
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{R}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{v:g}</text>')
    for d in range(-10, 3, 2):
        b.append(f'<text x="{sx(d):.0f}" y="{BOT+18}" class="xs" text-anchor="middle">{d:+d}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">detuning from low-pressure F=2 → F′=2 / GHz</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">cell mean P(F=2, mF=+2)</text>')
    b.append(f'<line x1="{sx(-3.75):.0f}" y1="{TOP}" x2="{sx(-3.75):.0f}" y2="{BOT}" class="thin"/>')
    b.append(f'<text x="{sx(-3.75)-5:.0f}" y="{BOT-8}" class="xs" text-anchor="end">uniform cell: −3.75</text>')
    # Four curves crowd into the band between P = 0.78 and P = 0.98, so no
    # label fits beside its own line. They go in the empty middle instead, in
    # curve order, each with a leader back to where its curve enters the frame.
    ranked = sorted(scans, key=lambda s: -max(s["P"]))
    for sc in ranked:
        pts = " ".join(f"{sx(d):.1f},{BOT-(BOT-TOP)*p:.1f}" for d, p in zip(sc["d"], sc["P"]))
        b.append(f'<polyline class="{"l" if sc["thick"] else "m"}" points="{pts}"/>')
        b.append(f'<circle cx="{sx(sc["best"]):.1f}" cy="{BOT-(BOT-TOP)*max(sc["P"]):.1f}" '
                 f'r="3" fill="var(--t0,#0d0d0d)"/>')
    for i, sc in enumerate(ranked):
        y = TOP + 96 + 22 * i
        cy = BOT - (BOT - TOP) * sc["P"][0]
        b.append(f'<line x1="{L+1}" y1="{cy:.1f}" x2="{L+12}" y2="{y-3:.1f}" class="dash"/>')
        b.append(f'<text x="{L+16}" y="{y:.1f}" class="xs">'
                 f'{sc["I"]:g} mW/cm², OD {sc["OD"]:.1f} — best {sc["best"]:+.2f} GHz, '
                 f'swing {sc["swing"]*100:.0f}%</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">At 30 mW/cm² the optimum does not move at all between OD 0.2 and OD 16. At 10 mW/cm² it moves 1 GHz — and toward resonance, not away from it.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">Detuning buys penetration, but only for a beam strong enough to bleach a path. A weak beam in a thick cell is set by its front layers.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">Every peak here is shallow. The marked maximum stands 1 to 12 per cent above the worst point in a twelve gigahertz window.</text>')
    return svg_wrap(W, H, "\n".join(b), "Cell-mean polarisation against detuning",
        "Cell-averaged stretched-state population against pump detuning, for a thin and a thick "
        "cell at two intensities, with beam depletion included. The marked maxima sit within one "
        "gigahertz of the uniform-cell answer, and every curve is shallow.", ("dtt", "dtd"))


def fig_od(temps: list[float]) -> str:
    W, H = 760, 396
    L, R, TOP, BOT = 96, 660, 60, 300
    tmin, tmax = 60.0, 160.0
    sx = lambda t: L + (R - L) * (t - tmin) / (tmax - tmin)
    ymax = 2.0                                        # log10 scale, 0.01 .. 100
    sy = lambda v: BOT - (BOT - TOP) * (math.log10(max(v, 1e-2)) + 2) / 4
    b = ['<text x="16" y="22" class="xs">OPTICAL DEPTH OF A 5.5 mm PATH</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">LOG SCALE</text>']
    for d in (0.01, 0.1, 1, 10, 100):
        y = sy(d)
        b.append(f'<line x1="{L}" y1="{y:.0f}" x2="{R}" y2="{y:.0f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.0f}" class="xs" text-anchor="end">{d:g}</text>')
    for t in range(60, 161, 20):
        b.append(f'<text x="{sx(t):.0f}" y="{BOT+18}" class="xs" text-anchor="middle">{t}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">cell temperature / °C</text>')
    b.append(f'<text x="26" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 26 {(TOP+BOT)/2})" text-anchor="middle">optical depth</text>')
    # Labelled low on the curves, in the empty lower-left corner: at the right-hand
    # end the two lines run close enough that a label sits on the other curve.
    for enr, cls, lab, tlab, dy, anc in ((ABUNDANCE_NATURAL, "m", "natural, 27.8% 87Rb", 88, 24, "start"),
                                         (0.693, "l", "enriched, 69.3%", 84, -12, "end")):
        pts = " ".join(f"{sx(t):.1f},{sy(optical_depth(t+273.15, enrichment=enr)):.1f}"
                       for t in temps)
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
        b.append(f'<text x="{sx(tlab)+(6 if anc == "start" else -6):.0f}" '
                 f'y="{sy(optical_depth(tlab+273.15, enrichment=enr))+dy:.1f}" '
                 f'class="xs" text-anchor="{anc}">{lab}</text>')
    b.append(f'<line x1="{L}" y1="{sy(3):.0f}" x2="{R}" y2="{sy(3):.0f}" class="dash"/>')
    b.append(f'<text x="{L+6}" y="{sy(3)-5:.0f}" class="xs">OD 3 — where an unpumped cell would go dark</text>')
    b.append(f'<line x1="{L}" y1="{sy(10):.0f}" x2="{R}" y2="{sy(10):.0f}" class="thin"/>')
    b.append(f'<text x="{L+6}" y="{sy(10)-5:.0f}" class="xs">OD 10 — where a pumped one does, at 30 mW/cm²</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">Density from the model Steck quotes, stated accurate to ±5% over 298–550 K. Cross section from T/04.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">The gap between the curves is one assumption: whether the cell is isotopically enriched. It moves the useful temperature by ~20 °C.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">The two thresholds differ because a polarised atom stops absorbing. Bleaching buys about 20 °C of headroom over the unpumped estimate.</text>')
    return svg_wrap(W, H, "\n".join(b), "Optical depth against cell temperature",
        "Optical depth of a 5.5 mm rubidium path against temperature, on a log scale, for "
        "natural and enriched 87Rb. Enrichment shifts the curve up by a factor of 2.5, moving "
        "the temperature at which the cell becomes optically thick down by about twenty degrees.",
        ("odt", "odd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    ENR = 0.693                       # see density_87; the alternative is reported too
    TEMPS = (80, 100, 120, 150)
    # The profile figure spans the knee instead of TEMPS: 80, 100 and 120 C all
    # come out flat at 0.98 and would plot as one line.
    runs = [(Tc, propagate(30.0, Tc + 273.15, 0.0, enrichment=ENR, nz=40, nt=2000))
            for Tc in (120, 140, 145, 150)]
    tables = [(Tc, propagate(30.0, Tc + 273.15, 0.0, enrichment=ENR, nz=40, nt=2000))
              for Tc in TEMPS]
    bleach = propagate(30.0, 150 + 273.15, 0.0, enrichment=ENR, nz=40, nt=2000,
                       snap_at=(0.05e-3, 0.1e-3, 0.2e-3, 0.5e-3, 1.0e-3))

    ds = [x * 0.25 for x in range(-40, 9)]
    scans = []
    for I, Tc in ((30, 80), (30, 150), (10, 80), (10, 150)):
        Ps = [propagate(I, Tc + 273.15, d * 1e9, enrichment=ENR,
                        nz=30, nt=1200)["mean"][-1] for d in ds]
        i = max(range(len(ds)), key=lambda k: Ps[k])
        scans.append({"I": I, "Tc": Tc, "thick": Tc == 150,
                      "OD": optical_depth(Tc + 273.15, enrichment=ENR),
                      "d": ds, "P": Ps, "best": ds[i],
                      "swing": (max(Ps) - min(Ps)) / max(Ps)})

    # Where the cell stops being uniform. The unpumped estimate says OD 3; a
    # pumped cell holds together much further, so the knee is worth locating.
    knee = []
    for Tc in range(120, 156, 5):
        r = propagate(30.0, Tc + 273.15, 0.0, enrichment=ENR, nz=40, nt=2000)
        knee.append({"Tc": Tc, "OD": round(r["OD0"], 2),
                     "back_decile": round(r["back"][-1], 4),
                     "mean": round(r["mean"][-1], 4),
                     "transmission": round(r["transmission"][-1], 4)})

    payload = {
        "vapour_model": "Steck eq. 1, liquid phase, stated +/-5% over 298-550 K",
        "abundance_natural": ABUNDANCE_NATURAL,
        "abundance_source": "Steck rev 2.3.4 Table 2, eta(87Rb) = 27.83(2)%",
        "cell_length_m": L_CELL, "sigma_m2": SIGMA_650,
        "gamma_g_per_s": GAMMA_G,
        "rate_per_mW_cm2": RATE_PER_MW_CM2,
        "absorber": "eight ground sublevels from scripts/solve_density_matrix.py",
        "enrichment_note": ("T/03's optical depths are 2.49x these at natural abundance, at "
                            "every temperature. A constant ratio is one temperature-independent "
                            "factor, and 0.2783 x 2.49 = 0.693 is an ordinary enrichment. It "
                            "could equally sit in a differently normalised density. Not "
                            "established here; both are reported."),
        "resolved_vs_line_strength": {
            f"{d:+.2f}": round(sum(channels(d * 1e9)[0].values()) / len(dm.GROUND), 4)
            for d in (0.0, -3.5, -6.575, -10.0)},
        "optical_depth": {
            str(Tc): {"natural": round(optical_depth(Tc + 273.15), 4),
                      "enriched_0693": round(optical_depth(Tc + 273.15, enrichment=ENR), 4),
                      "enriched_resolved_at_0":
                          round(optical_depth(Tc + 273.15, enrichment=ENR, detuning=0.0), 4)}
            for Tc in TEMPS},
        "after_1ms_30mW_enriched": {
            str(Tc): {"OD": round(r["OD0"], 3), "front": round(r["front"][-1], 4),
                      "back_decile": round(r["back"][-1], 4), "mean": round(r["mean"][-1], 4),
                      "transmission": round(r["transmission"][-1], 4)}
            for Tc, r in tables},
        "after_1ms_30mW_natural": {
            str(Tc): {k: round(v, 4) for k, v in
                      (lambda r: {"OD": r["OD0"], "front": r["front"][-1],
                                  "back_decile": r["back"][-1], "mean": r["mean"][-1],
                                  "transmission": r["transmission"][-1]})(
                          propagate(30.0, Tc + 273.15, 0.0, nz=40, nt=2000)).items()}
            for Tc in TEMPS},
        "bleaching_front_150C": {f"{s['t']*1e3:g}ms":
                                 {"front": round(s["P"][0], 4),
                                  "mid": round(s["P"][len(s["P"]) // 2], 4),
                                  "back": round(s["P"][-1], 4)} for s in bleach["snaps"]},
        "detuning_with_propagation": {
            f'{sc["I"]}mW_{sc["Tc"]}C': {"OD": round(sc["OD"], 2), "best_GHz": sc["best"],
                                         "peak": round(max(sc["P"]), 4),
                                         "swing_over_window": round(sc["swing"], 4)}
            for sc in scans},
        "uniform_cell_optimum_GHz": {"30": -3.75, "10": -3.75, "5": -3.5, "1": -3.0,
                                     "note": "T/05's solve on this 0.25 GHz grid; it "
                                             "reports -3.5 on its own 0.5 GHz grid"},
        "uniformity_knee": knee,
    }
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-cell-profile.svg": fig_profile(runs),
        OUT_SVG / "rb87-cell-bleach.svg": fig_bleach(bleach, 150),
        OUT_SVG / "rb87-cell-detuning.svg": fig_detuning(scans),
        OUT_SVG / "rb87-optical-depth.svg": fig_od([60 + 2 * i for i in range(51)]),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    for Tc, r in tables:
        print(f"  {Tc:>3} C  OD {r['OD0']:5.2f}  front {r['front'][-1]:.3f}  "
              f"back {r['back'][-1]:.3f}  mean {r['mean'][-1]:.3f}  "
              f"T {r['transmission'][-1]:.3f}")
    for sc in scans:
        print(f"  {sc['I']:>2} mW/cm2 {sc['Tc']:>3} C  OD {sc['OD']:5.2f}  "
              f"best {sc['best']:+.2f} GHz  swing {sc['swing']*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
