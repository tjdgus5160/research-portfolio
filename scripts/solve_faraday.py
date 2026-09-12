#!/usr/bin/env python3
"""How the spin is actually read: Faraday rotation of the probe.

Everything from T/01 to T/08 prepares a polarisation and lets it precess. None
of it computes what a detector sees. This does.

A polarised vapour is circularly birefringent: sigma+ and sigma- light meet
different refractive indices because they are absorbed by different numbers of
atoms. The two helicities that make up linearly polarised light therefore
accumulate different phases, and the plane of polarisation turns.

    theta = (pi nu l / c) [n+(nu) - n-(nu)]              Seltzer eq. 2.68
    n(nu) = 1 + (n r_e c^2 f / 4nu) Im[V(nu - nu_0)]     Seltzer eq. 2.81
    theta = (pi/2) l n r_e c P_x
            ( -f_D1 Im[V(nu-nu_D1)] + (1/2) f_D2 Im[V(nu-nu_D2)] )
                                                         Seltzer eq. 2.87

The thing worth noticing is that the rotation follows Im[V], the DISPERSIVE
part of the line, while absorption follows Re[V]. Dispersion is odd about
resonance and absorption is even. So the rotation vanishes exactly on line
centre, where the absorption is largest, and the useful signal lives in the
wings.

That sets up a trade-off with an exact answer: detune too little and the probe
is absorbed, too much and the rotation dies as 1/detuning. The transmitted
signal theta*exp(-OD) is maximised at an optical depth of exactly one half, and
that is independent of density, linewidth, oscillator strength and cell length.

    python3 scripts/solve_faraday.py [--check]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "faraday.json"

K_B = 1.380649e-23
C = 299792458.0
R_E = 2.8179403262e-15            # Steck table 1, classical electron radius
LAM_D1 = 794.978851156e-9         # Steck table 4
LAM_D2 = 780.241209686e-9         # Steck table 3
NU_D1, NU_D2 = C / LAM_D1, C / LAM_D2
F_D1 = 0.34231                    # Steck table 4, absorption oscillator strength
F_D2 = 0.69577                    # Steck table 3
GAMMA_L = 14.19e9                 # pressure-broadened FWHM at 650 Torr, T/02
L_CELL = 5.5e-3
T_MELT = 312.46
ENRICHED = 0.693                  # see T/06; natural abundance is also reported


def n_rb87(T: float, enrichment: float = ENRICHED) -> float:
    e = (4.312 - 4040.0 / T) if T > T_MELT else (4.857 - 4215.0 / T)
    return 10 ** (2.881 + e) * 133.322368 / (K_B * T) * enrichment


# ── the complex Lorentzian ────────────────────────────────────────────────
# Seltzer eq. 2.82. Its real and imaginary parts are a Kramers-Kronig pair, so
# one lineshape carries both absorption and dispersion. He states the condition
# for replacing the Voigt profile with it: Gamma_L >> Gamma_G. Here the
# collisional width is 14.19 GHz against a 0.51 GHz Doppler width, a ratio of
# 28, so the substitution is safe -- and that ratio is printed by --check.
def im_L(d: float) -> float:
    """Dispersive part. Odd in d, so it is zero on resonance."""
    return (d / math.pi) / (d * d + (GAMMA_L / 2) ** 2)


def re_L(d: float) -> float:
    """Absorptive part. Even in d, so it is largest on resonance."""
    return (GAMMA_L / (2 * math.pi)) / (d * d + (GAMMA_L / 2) ** 2)


def theta(nu: float, n: float, P_x: float = 1.0) -> float:
    """Seltzer eq. 2.87, in radians.

    The two D lines enter with opposite sign: a probe between them sees the
    rotations partly cancel, and the useful side of each line is the one facing
    away from the other.
    """
    return ((math.pi / 2) * L_CELL * n * R_E * C * P_x
            * (-F_D1 * im_L(nu - NU_D1) + 0.5 * F_D2 * im_L(nu - NU_D2)))


def optical_depth(nu: float, n: float) -> float:
    """Both lines, same normalisation as the index above.

    On D1 line centre with the D2 term dropped this reduces to
    sigma = 2 r_e c f / Gamma_L, which is 4.0759e-13 cm^2 -- the number T/04
    reached from the oscillator strength by a different route. The two agree to
    six figures, which is the check that the dispersion and absorption here are
    normalised consistently.
    """
    return math.pi * R_E * C * L_CELL * n * (F_D1 * re_L(nu - NU_D1)
                                             + F_D2 * re_L(nu - NU_D2))


def signal(nu: float, n: float, P_x: float = 1.0) -> float:
    """What survives the trip: rotation times transmission."""
    return theta(nu, n, P_x) * math.exp(-optical_depth(nu, n))


def best_detuning(n: float, span: float = 600e9, step: float = 2e7) -> dict:
    """Scan the blue side of D2 for the largest transmitted signal.

    Blue rather than red because the D1 line sits 7.12 THz to the red and its
    rotation has the opposite sign, so the red side of D2 is where the two
    partly cancel.
    """
    k = 1
    best = (0.0, 0.0)
    while k * step <= span:
        d = k * step
        s = abs(signal(NU_D2 + d, n))
        if s > best[0]:
            best = (s, d)
        k += 1
    d = best[1]
    return {"detuning_Hz": d, "signal_rad": signal(NU_D2 + d, n),
            "theta_rad": theta(NU_D2 + d, n), "OD": optical_depth(NU_D2 + d, n),
            "at_scan_edge": abs(d - span) < step}


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
  .xs,.sm{{paint-order:stroke fill;stroke:var(--t3,#d7d7d7);stroke-width:3px;
    stroke-linejoin:round}}
</style>
{body}
</svg>
'''


def _axes(b, L, R, TOP, BOT, ys, xs, ylab, xlab):
    for lab, y in ys:
        b.append(f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" class="dash"/>')
        b.append(f'<text x="{L-8}" y="{y+4:.1f}" class="xs" text-anchor="end">{lab}</text>')
    for lab, x in xs:
        b.append(f'<text x="{x:.1f}" y="{BOT+18}" class="xs" text-anchor="middle">{lab}</text>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{R}" y2="{BOT}" class="thin"/>')
    b.append(f'<line x1="{L}" y1="{BOT}" x2="{L}" y2="{TOP}" class="thin"/>')
    b.append(f'<text x="{(L+R)/2}" y="{BOT+38}" class="sm" text-anchor="middle">{xlab}</text>')
    b.append(f'<text x="24" y="{(TOP+BOT)/2}" class="sm" '
             f'transform="rotate(-90 24 {(TOP+BOT)/2})" text-anchor="middle">{ylab}</text>')


def fig_lineshape(T: float) -> str:
    """Dispersion is odd, absorption is even. That is the whole entry in one plot."""
    W, H = 760, 414
    L, R, TOP, BOT = 100, 648, 62, 316
    n = n_rb87(T)
    span = 60e9
    sx = lambda d: L + (R - L) * (d + span) / (2 * span)
    mid = (TOP + BOT) / 2
    tmax = 0.30
    sy = lambda v: mid - (mid - TOP) * v / tmax
    b = ['<text x="16" y="22" class="xs">THE ROTATION IS ZERO WHERE THE ABSORPTION IS LARGEST</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">{T-273.15:.0f} °C, P = 1, D2 부근</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:+g}" if v else "0", sy(v)) for v in (-0.3, -0.15, 0, 0.15, 0.3)],
          [(f"{d:+g}" if d else "D2", sx(d * 1e9)) for d in (-60, -30, 0, 30, 60)],
          "rad", "D2 선 중심에서의 detuning / GHz")
    N = 900
    ds = [-span + 2 * span * k / N for k in range(N + 1)]
    b.append('<polyline class="l" points="'
             + " ".join(f"{sx(d):.1f},{sy(theta(NU_D2+d, n)):.1f}" for d in ds) + '"/>')
    b.append('<polyline class="m" points="'
             + " ".join(f"{sx(d):.1f},{sy(optical_depth(NU_D2+d, n)*0.15):.1f}" for d in ds) + '"/>')
    b.append(f'<line x1="{sx(0):.0f}" y1="{TOP}" x2="{sx(0):.0f}" y2="{BOT}" class="dash"/>')
    b.append(f'<circle cx="{sx(0):.1f}" cy="{sy(0):.1f}" r="3.5" fill="var(--t0,#0d0d0d)"/>')
    b.append(f'<text x="{sx(2.5e9):.0f}" y="{sy(0)-9:.0f}" class="xs">'
             f'θ = 0 정확히 여기서</text>')
    b.append(f'<text x="{sx(-34e9):.0f}" y="{sy(theta(NU_D2-34e9,n))-9:.0f}" class="xs">'
             f'θ — 회전 (분산형, 홀함수)</text>')
    b.append(f'<text x="{sx(-24e9):.0f}" y="{sy(0.255):.0f}" class="xs">'
             f'광학 깊이 (흡수형, 짝함수) ×0.15</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">굴절률의 실수부와 허수부는 Kramers–Kronig 쌍입니다. 하나가 흡수면 다른 하나가 분산이고, 둘은 같은 선 하나에서 나옵니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">흡수가 가장 큰 곳에서 회전이 정확히 0입니다. 선 중심에 프로브를 두면 신호가 없습니다 — 빛만 잃습니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">쓸 만한 신호는 날개에 있고, 어디까지 물러날지가 이 항목이 푸는 문제입니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Dispersion and absorption near the D2 line",
        "The Faraday rotation angle and the optical depth against probe detuning. The rotation "
        "is an odd function that passes through zero exactly on resonance, where the absorption "
        "is at its maximum.", ("lst", "lsd"))


def fig_signal(temps: list[float]) -> str:
    """The trade-off, and where each temperature wants to sit."""
    W, H = 760, 414
    L, R, TOP, BOT = 100, 640, 62, 316
    span = 120e9
    sx = lambda d: L + (R - L) * d / span
    smax = 0.70
    sy = lambda v: BOT - (BOT - TOP) * v / smax
    b = ['<text x="16" y="22" class="xs">WHAT SURVIVES THE TRIP — ROTATION × TRANSMISSION</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">BLUE SIDE OF D2, P = 1</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0, 0.2, 0.4, 0.6)],
          [(f"{d:g}", sx(d * 1e9)) for d in (0, 30, 60, 90, 120)],
          "θ·e^(−OD) / rad", "D2에서 파랑쪽 detuning / GHz")
    N = 600
    for i, Tc in enumerate(temps):
        n = n_rb87(Tc + 273.15)
        pts = " ".join(f"{sx(span*k/N):.1f},{sy(abs(signal(NU_D2+span*k/N, n))):.1f}"
                       for k in range(1, N + 1))
        b.append(f'<polyline class="{"l" if Tc == max(temps) else "m"}" points="{pts}"/>')
        bd = best_detuning(n)
        b.append(f'<circle cx="{sx(bd["detuning_Hz"]):.1f}" '
                 f'cy="{sy(abs(bd["signal_rad"])):.1f}" r="3" fill="var(--t0,#0d0d0d)"/>')
        b.append(f'<text x="{sx(bd["detuning_Hz"])+7:.0f}" '
                 f'y="{sy(abs(bd["signal_rad"]))-6:.0f}" class="xs">'
                 f'{Tc:g} °C — OD {bd["OD"]:.2f}</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">공명에 가까우면 회전은 크지만 빛이 통과하지 못하고, 멀어지면 빛은 살지만 회전이 1/detuning으로 죽습니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">각 온도의 최적점에 찍은 점이 전부 광학 깊이 0.4~0.5에 모입니다. 우연이 아닙니다 — 다음 그림이 그것입니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">신호 자체는 온도를 올릴수록 계속 커집니다. 감도가 그렇지 않은 이유는 T₂가 함께 무너지기 때문이고, 그것은 여기서 다루지 않습니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Transmitted rotation signal against detuning",
        "The product of rotation angle and transmission, against probe detuning, at four cell "
        "temperatures. Each curve has a single maximum, and all of the maxima sit at an optical "
        "depth near one half.", ("sgt", "sgd"))


def fig_half(densities: list[float]) -> str:
    """The optimum optical depth is 1/2, and it does not depend on anything."""
    W, H = 760, 400
    L, R, TOP, BOT = 100, 636, 62, 306
    sx = lambda n: L + (R - L) * (math.log10(n) - 16) / 6.0
    sy = lambda v: BOT - (BOT - TOP) * v / 0.8
    b = ['<text x="16" y="22" class="xs">THE OPTIMUM IS AN OPTICAL DEPTH OF ONE HALF</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">밀도를 여섯 자릿수에 걸쳐</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0, 0.25, 0.5, 0.75)],
          [(f"10^{e}", sx(10.0 ** e)) for e in (16, 18, 20, 22)],
          "최적점에서의 광학 깊이", "⁸⁷Rb 수밀도 / m⁻³")
    pts = []
    for n in densities:
        bd = best_detuning(n, span=900e9, step=5e7)
        if bd["at_scan_edge"]:
            continue
        pts.append(f"{sx(n):.1f},{sy(bd['OD']):.1f}")
    b.append(f'<polyline class="l" points="{" ".join(pts)}"/>')
    b.append(f'<line x1="{L}" y1="{sy(0.5):.1f}" x2="{R}" y2="{sy(0.5):.1f}" class="thin"/>')
    b.append(f'<text x="{L+8}" y="{sy(0.5)-7:.0f}" class="xs">OD = 1/2 — 해석적으로 유도되는 값</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">선에서 충분히 멀어지면 θ ≈ An/δ, OD ≈ Bn/δ². 곱 (An/δ)·e^(−Bn/δ²)을 δ로 미분해 0으로 놓으면 δ² = 2Bn이고,</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">그것을 OD = Bn/δ²에 넣으면 B와 n이 약분되어 정확히 1/2이 남습니다. 선폭도 진동자 세기도 셀 길이도 B 안에서 사라집니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">왼쪽 끝이 1/2에 못 미치는 것은 그 근사가 깨지기 때문입니다 — 최적 detuning이 선폭의 절반과 비슷해집니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "The optimum optical depth",
        "The optical depth at the best probe detuning, against vapour density over six decades. "
        "It approaches one half from below and stays there, which is what the far-detuned "
        "derivation predicts.", ("hft", "hfd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    TEMPS = [80, 100, 120, 150]
    DOPPLER_D2 = 0.512e9        # T/02, 100 C; the condition on eq. 2.82
    rows = {}
    for Tc in TEMPS:
        n = n_rb87(Tc + 273.15)
        bd = best_detuning(n)
        rows[str(Tc)] = {
            "n87_m3": n,
            "best_detuning_GHz": round(bd["detuning_Hz"] / 1e9, 3),
            "theta_mrad": round(bd["theta_rad"] * 1e3, 2),
            "OD_at_optimum": round(bd["OD"], 4),
            "signal_mrad": round(bd["signal_rad"] * 1e3, 2),
            "theta_on_D2_centre_mrad": round(theta(NU_D2, n) * 1e3, 4),
            "OD_on_D2_centre": round(optical_depth(NU_D2, n), 3)}

    sweep = {}
    for e in (16, 17, 18, 19, 20, 21):
        bd = best_detuning(10.0 ** e, span=900e9, step=5e7)
        sweep[f"1e{e}"] = {"OD": round(bd["OD"], 4),
                           "detuning_GHz": round(bd["detuning_Hz"] / 1e9, 1),
                           "at_scan_edge": bd["at_scan_edge"]}

    sigma_here = 2 * R_E * C * F_D1 / GAMMA_L
    payload = {
        "equations": ("Seltzer thesis eqs. 2.63-2.69 (rotation from circular birefringence), "
                      "2.73-2.81 (Kramers-Kronig to the index), 2.82 (complex Lorentzian), "
                      "2.87 (the D1/D2 result). Constants from Steck tables 3 and 4."),
        "validity_of_complex_lorentzian": {
            "Gamma_L_Hz": GAMMA_L, "Doppler_FWHM_Hz": DOPPLER_D2,
            "ratio": round(GAMMA_L / DOPPLER_D2, 1),
            "note": "Seltzer states the substitution needs Gamma_L >> Gamma_G."},
        "cross_check_against_T04": {
            "sigma_peak_D1_cm2": sigma_here * 1e4,
            "T04_published_cm2": 4.076e-13,
            "ratio": round(sigma_here * 1e4 / 4.076e-13, 6),
            "note": ("T/04 reached this from the oscillator strength and a Lorentzian "
                     "normalisation. This reaches it from the refractive index through "
                     "Kramers-Kronig. Different route, same number.")},
        "on_D2_line_centre": {
            "note": ("The rotation is exactly zero on resonance because Im[L] is odd. What "
                     "little is left at 100 C is the far tail of D1, 7.12 THz away."),
            "residual_mrad": round(theta(NU_D2, n_rb87(373.15)) * 1e3, 4)},
        "by_temperature": rows,
        "optimum_is_half": {
            "analytic": ("Far from the line theta ~ A n/d and OD ~ B n/d^2. Setting "
                         "d/dd [ (An/d) exp(-Bn/d^2) ] = 0 gives d^2 = 2Bn, and OD = "
                         "Bn/d^2 = 1/2 -- free of n, Gamma, f and l."),
            "numeric": sweep},
        "D1_D2_separation_THz": round((NU_D2 - NU_D1) / 1e12, 4),
    }
    dens = [10.0 ** (16 + 6 * k / 60) for k in range(61)]
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-faraday-lineshape.svg": fig_lineshape(373.15),
        OUT_SVG / "rb87-faraday-signal.svg": fig_signal(TEMPS),
        OUT_SVG / "rb87-faraday-half.svg": fig_half(dens),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    print(f"  Gamma_L / Doppler = {GAMMA_L/DOPPLER_D2:.1f}  (complex Lorentzian valid)")
    print(f"  sigma_peak(D1) = {sigma_here*1e4:.4e} cm2 vs T/04's 4.076e-13  "
          f"ratio {sigma_here*1e4/4.076e-13:.6f}")
    print(f"  on D2 centre at 100 C: theta = {theta(NU_D2, n_rb87(373.15))*1e3:+.4f} mrad")
    for Tc in TEMPS:
        r = rows[str(Tc)]
        print(f"  {Tc:>3} C  best {r['best_detuning_GHz']:>6.2f} GHz  "
              f"theta {r['theta_mrad']:>7.1f} mrad  OD {r['OD_at_optimum']:.3f}  "
              f"signal {r['signal_mrad']:>7.1f} mrad")
    print("  OD at optimum vs density: "
          + ", ".join(f"{k}:{v['OD']:.3f}" for k, v in sweep.items() if not v["at_scan_edge"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
