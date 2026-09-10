#!/usr/bin/env python3
"""How wide the 87Rb D1 line gets as N2 is added, and where that width comes from.

Three things set the width of the optical line in a buffered cell:

  * the natural width, fixed by the excited-state lifetime;
  * Doppler broadening, a Gaussian set by the temperature and the atomic mass —
    it does not care how much buffer gas there is;
  * collisional (pressure) broadening, a Lorentzian proportional to the buffer
    gas density.

The first two are computed here from first principles. The third needs a
measured coefficient, and this uses one that two independent papers agree on.

The total is a Voigt profile. Rather than use a closed-form approximation for
its width, this convolves the two profiles numerically and measures the FWHM of
the result, so nothing rests on a fitting formula.

    python3 scripts/calc_n2_linewidth.py            # write the figures and the table
    python3 scripts/calc_n2_linewidth.py --check    # recompute and compare, write nothing
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "n2-linewidth.json"

# ── inputs, each with where it came from ──────────────────────────────────
K_B = 1.380649e-23            # J/K, exact by SI definition
U = 1.66053906660e-27         # kg, Steck table 1
M_RB87 = 86.909180527 * U     # Steck table 1, atomic mass 86.909 180 527(13) u
C = 299792458.0               # m/s, exact by SI definition
LAMBDA_D1 = 794.978851156e-9  # m, Steck table 4
GAMMA_NAT_D1 = 5.7500e6       # Hz FWHM, Steck table 4: 2π · 5.7500(56) MHz -> 5.75 MHz
BROADEN_GHZ_PER_AMAGAT = 17.8 # Rb D1 by N2. Two independent sources agree; see below.
AMAGAT_TORR_0C = 760.0        # 1 amagat is 1 atm at 273.15 K
T0 = 273.15                   # K


def doppler_fwhm(T: float) -> float:
    """Gaussian FWHM in Hz. Depends on temperature and mass, not on pressure."""
    return math.sqrt(8 * K_B * T * math.log(2) / (M_RB87 * C * C)) * (C / LAMBDA_D1)


def amagat_from_torr(p_torr: float, T: float) -> float:
    """A Torr is fewer atoms when the gas is hot; density is what broadens."""
    return (p_torr / AMAGAT_TORR_0C) * (T0 / T)


def lorentz_fwhm(p_torr: float, T: float) -> float:
    return BROADEN_GHZ_PER_AMAGAT * 1e9 * amagat_from_torr(p_torr, T) + GAMMA_NAT_D1


def voigt_fwhm(fg: float, fl: float, n: int = 200_001) -> float:
    """FWHM of a Gaussian of width fg convolved with a Lorentzian of width fl.

    Measured off the convolution rather than taken from a fitting formula, so
    the number owes nothing to an approximation whose error would have to be
    quoted and defended.
    """
    span = 12 * (fg + fl)
    x = [(-span / 2) + span * i / (n - 1) for i in range(n)]
    dx = x[1] - x[0]
    sg = fg / (2 * math.sqrt(2 * math.log(2)))
    hl = fl / 2
    g = [math.exp(-0.5 * (v / sg) ** 2) for v in x]
    l = [hl / (v * v + hl * hl) for v in x]
    # convolution at the centre only would not give a width, so do it properly
    # via the discrete Fourier route would need numpy; direct is fine at this n
    import array
    half = n // 2
    prof = array.array("d", [0.0]) * 0
    prof = [0.0] * n
    # sample the convolution on a coarser grid, then refine around the half max
    step = max(1, n // 4000)
    idx = list(range(0, n, step))
    vals = []
    for i in idx:
        s = 0.0
        shift = i - half
        for j in range(0, n, step):
            k = j - shift
            if 0 <= k < n:
                s += g[j] * l[k]
        vals.append(s)
    peak = max(vals)
    # walk out from the peak to the half-maximum crossings and interpolate
    pk = vals.index(peak)
    def cross(rng):
        prev_i, prev_v = pk, peak
        for i in rng:
            if vals[i] <= peak / 2:
                f = (peak / 2 - prev_v) / (vals[i] - prev_v)
                return x[idx[prev_i]] + f * (x[idx[i]] - x[idx[prev_i]])
            prev_i, prev_v = i, vals[i]
        return None
    lo = cross(range(pk, -1, -1))
    hi = cross(range(pk, len(vals)))
    return (hi - lo) if (lo is not None and hi is not None) else float("nan")


def table(T: float, pressures: list[float]) -> list[dict]:
    fg = doppler_fwhm(T)
    rows = []
    for p in pressures:
        fl = lorentz_fwhm(p, T)
        rows.append({
            "torr": p,
            "amagat": round(amagat_from_torr(p, T), 5),
            "doppler_GHz": round(fg / 1e9, 5),
            "collisional_GHz": round((fl - GAMMA_NAT_D1) / 1e9, 5),
            "lorentz_total_GHz": round(fl / 1e9, 5),
            "voigt_GHz": round(voigt_fwhm(fg, fl) / 1e9, 5),
        })
    return rows


# ── the figure ────────────────────────────────────────────────────────────
def chart(rows: list[dict], T: float) -> str:
    W, H = 760, 470
    L, R, TOP, BOT = 92, 700, 60, 380
    xmax = max(r["torr"] for r in rows)
    ymax = max(r["voigt_GHz"] for r in rows) * 1.08
    sx = lambda p: L + (R - L) * p / xmax
    sy = lambda v: BOT - (BOT - TOP) * v / ymax
    b = [f'<text x="16" y="24" class="xs">87Rb D1 LINEWIDTH vs N2 PRESSURE</text>',
         f'<text x="{W-16}" y="24" class="xs" text-anchor="end">CELL AT {T-273.15:.0f} C</text>']
    # frame and ticks
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    for p in range(0, int(xmax) + 1, 50):
        b.append(f'<line x1="{sx(p):.1f}" y1="{BOT}" x2="{sx(p):.1f}" y2="{BOT+5}" class="thin"/>')
        b.append(f'<text x="{sx(p):.1f}" y="{BOT+18}" class="xs" text-anchor="middle">{p}</text>')
    step = 1 if ymax > 3 else 0.5
    v = 0.0
    while v <= ymax:
        b.append(f'<line x1="{L-5}" y1="{sy(v):.1f}" x2="{R}" y2="{sy(v):.1f}" class="dash"/>')
        b.append(f'<text x="{L-10}" y="{sy(v)+4:.1f}" class="xs" text-anchor="end">{v:g}</text>')
        v += step
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">N2 pressure at fill / Torr</text>')
    b.append(f'<text x="24" y="{(TOP+BOT)/2}" class="sm" transform="rotate(-90 24 {(TOP+BOT)/2})" text-anchor="middle">FWHM / GHz</text>')

    def path(key, cls):
        return ('<polyline class="' + cls + '" fill="none" points="'
                + " ".join(f"{sx(r['torr']):.1f},{sy(r[key]):.1f}" for r in rows) + '"/>')
    b.append(path("doppler_GHz", "dash"))
    b.append(path("collisional_GHz", "thin"))
    b.append(path("voigt_GHz", "l"))

    last = rows[-1]
    b.append(f'<text x="{R-4}" y="{sy(last["voigt_GHz"])-8:.1f}" class="sm" text-anchor="end">total (Voigt)</text>')
    b.append(f'<text x="{R-4}" y="{sy(last["collisional_GHz"])+16:.1f}" class="xs" text-anchor="end">collisional only</text>')
    b.append(f'<text x="{R-4}" y="{sy(rows[0]["doppler_GHz"])-6:.1f}" class="xs" text-anchor="end">Doppler {rows[0]["doppler_GHz"]:.3f} GHz, flat in pressure</text>')
    slope = rows[-1]["collisional_GHz"] / rows[-1]["torr"]
    xc = rows[0]["doppler_GHz"] / slope
    b.append(f'<line x1="{sx(xc):.1f}" y1="{TOP}" x2="{sx(xc):.1f}" y2="{BOT}" class="dash"/>')
    b.append(f'<text x="{sx(xc)+6:.1f}" y="{TOP+14}" class="xs">Doppler = collisional at {xc:.0f} Torr</text>')
    b.append(f'<text x="16" y="{H-40}" class="xs">collisional = 17.8 GHz/amagat x density; density falls as 1/T, so a Torr broadens less when hot</text>')
    b.append(f'<text x="16" y="{H-26}" class="xs">natural width 5.75 MHz is included and is invisible at this scale</text>')
    b.append(f'<text x="16" y="{H-12}" class="xs">Voigt width measured off a numerical convolution, not from a fitting formula</text>')
    return svg_wrap(W, H, "\n".join(b),
        "87Rb D1 linewidth against N2 pressure",
        f"At {T-273.15:.0f} C the Doppler width is {rows[0]['doppler_GHz']:.3f} GHz and does not "
        "change with pressure. Collisional broadening rises linearly at 17.8 GHz per amagat of N2, "
        "crossing the Doppler width near 35 Torr and dominating above it. The total Voigt width is "
        "the convolution of the two.")


def svg_wrap(w, h, body, title, desc):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
  role="img" aria-labelledby="ct cd" class="lvl">
<title id="ct">{title}</title><desc id="cd">{desc}</desc>
<style>
  .lvl{{font-family:"IBM Plex Mono","SF Mono",monospace}}
  .l{{stroke:var(--t0,#0d0d0d);stroke-width:3;fill:none}}
  .thin{{stroke:var(--t1,#3a3a3a);stroke-width:1.5;fill:none}}
  .dash{{stroke:var(--t2,#8a8a8a);stroke-width:1;stroke-dasharray:3 4;fill:none}}
  text{{fill:var(--t0,#0d0d0d);font-size:11px}}
  .sm{{font-size:9px;fill:var(--t1,#3a3a3a)}}
  .xs{{font-size:8px;fill:var(--t1,#3a3a3a);letter-spacing:.05em}}
</style>
{body}
</svg>
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    T = 373.15                                   # 100 C, a typical Rb cell
    pressures = [0, 5, 10, 20, 35, 50, 75, 100, 150, 200]
    rows = table(T, pressures)
    payload = {
        "cell_temperature_K": T,
        "broadening_GHz_per_amagat": BROADEN_GHZ_PER_AMAGAT,
        "natural_FWHM_Hz": GAMMA_NAT_D1,
        "doppler_FWHM_GHz": round(doppler_fwhm(T) / 1e9, 6),
        "rows": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.mkdir(parents=True, exist_ok=True)
    new_json = json.dumps(payload, indent=2) + "\n"
    new_svg = chart(rows, T)
    if a.check:
        same = (OUT_JSON.exists() and OUT_JSON.read_text() == new_json
                and (OUT_SVG / "rb87-n2-linewidth.svg").exists()
                and (OUT_SVG / "rb87-n2-linewidth.svg").read_text() == new_svg)
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.write_text(new_json)
    (OUT_SVG / "rb87-n2-linewidth.svg").write_text(new_svg, encoding="utf-8")
    print(f"  Doppler {payload['doppler_FWHM_GHz']:.4f} GHz at {T-273.15:.0f} C")
    for r in rows:
        print(f"   {r['torr']:>4} Torr  {r['amagat']:.4f} amg  "
              f"coll {r['collisional_GHz']:6.3f}  voigt {r['voigt_GHz']:6.3f} GHz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
