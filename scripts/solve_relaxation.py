#!/usr/bin/env python3
"""Compute the relaxation rate that every entry since T/03 has assumed.

Gamma_g = 170 1/s arrived as a model input in a submitted calculation, was
carried unchanged through T/03, T/04, T/05, T/06 and T/07, and was flagged in
every one of their unknown lists as the number the answers stand or fall with.
It was never computed here because the cross sections were missing.

Seltzer's thesis Table A.2 has all of them. So this computes the rate instead
of assuming it, and the answer is not 170.

    1/T1 = (1/q)(R_SD + R_OP + R_pr) + R_wall                 Seltzer eq. 2.133
    1/T2 = 1/T1 + R_SE/q_SE + R_gr                            Seltzer eq. 2.135
    R    = n sigma v,   v = sqrt(8 kB T / pi M),  1/M = 1/m + 1/m'
                                                  Seltzer eqs. 2.130-2.132
    1/T_wall = D (pi/R)^2  (sphere)                           Seltzer eq. 2.151
    D = D_0 p_0/p                                             Seltzer eq. 2.146 ff

The pumping and probe terms are left out: this is the relaxation the pump has
to fight, which is what Gamma_g means in the rate equation of T/04.

    python3 scripts/solve_relaxation.py [--check]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "relaxation.json"

K_B = 1.380649e-23
U = 1.66053906660e-27
AMG = 2.69e25                 # m^-3. Seltzer footnote: 1 amg = 2.69e19 cm^-3
M_RB = 86.909180520 * U       # Steck table 2
M_N2 = 28.0134 * U
I_NUC = 1.5
W_HF = 2 * math.pi * 6.834682610904e9

# ── Seltzer thesis, Table A.2, rubidium column. cm^2 -> m^2, cm^2/s -> m^2/s ──
SIG_SD_N2 = 1e-22 * 1e-4      # Rb-N2 spin destruction   (Kadlecek 1998; Allred 2002)
SIG_SD_SELF = 1.6e-17 * 1e-4  # Rb-Rb spin destruction   (Walker & Happer 1997; Kadlecek 1998)
SIG_SE_SELF = 1.9e-14 * 1e-4  # Rb-Rb spin exchange      (Ressler 1969; Aleksandrov 1999)
SIG_Q_N2 = 5.8e-15 * 1e-4     # Rb(5P1/2)-N2 quenching   (McGillis & Krause; Hrycyshyn & Krause)
D0_N2 = 0.19 * 1e-4           # Rb in N2 at 1 amg, 273 K (Franz & Sooriamoorthi; Franz & Volk)

N_AM = 0.7969                 # this cell: 650 Torr filled at 293.15 K
L_CELL = 5.5e-3               # interior. 7.5 mm outer cube less ~1 mm walls; see the entry
T_MELT = 312.46


def v_rel(T: float, m1: float, m2: float) -> float:
    """Seltzer eqs. 2.131-2.132."""
    M = 1.0 / (1.0 / m1 + 1.0 / m2)
    return math.sqrt(8 * K_B * T / (math.pi * M))


def n_rb(T: float) -> float:
    """Steck eq. 1 / Seltzer table A.3 -- the two agree digit for digit."""
    e = (4.312 - 4040.0 / T) if T > T_MELT else (4.857 - 4215.0 / T)
    return 10 ** (2.881 + e) * 133.322368 / (K_B * T)


def q_slow(P: float) -> float:
    """Nuclear slowing-down factor, I = 3/2. Seltzer table 2.5.

    This is the quantity T/04 carried as `n_cycle = 10`: the number of photon
    scattering events a pumping cycle costs, because the nucleus holds angular
    momentum that the electron spin has to drag around with it. It is not a free
    parameter and it is not 10 -- it runs from 6 unpolarised to 4 fully polarised.
    """
    return (6 + 2 * P * P) / (1 + P * P)


def diffusion(T: float, n_am: float = N_AM) -> float:
    """D at this temperature and fill density.

    Seltzer quotes D_0 at 1 amg and 273 K and gives only the pressure scaling
    D = D_0 p_0/p. At FIXED DENSITY the temperature scaling follows from
    D = (1/3) lambda v: the mean free path is fixed, so D goes as sqrt(T). The
    usual literature form D = D_0 (T/T_0)^{3/2} (p_0/p) gives the same thing
    once p is taken at temperature T, since p scales as T at fixed density.
    """
    return D0_N2 / n_am * math.sqrt(T / 273.15)


def rates(T: float, n_am: float = N_AM, L: float = L_CELL, P: float = 1.0) -> dict:
    n = n_rb(T)
    r_sd_n2 = n_am * AMG * SIG_SD_N2 * v_rel(T, M_RB, M_N2)
    r_sd_self = n * SIG_SD_SELF * v_rel(T, M_RB, M_RB)
    r_se = n * SIG_SE_SELF * v_rel(T, M_RB, M_RB)
    # Seltzer solves the sphere (eq. 2.151) and says "similar solutions may be
    # obtained for arbitrary cell geometry". For a box the lowest diffusion mode
    # is D pi^2 (1/a^2 + 1/b^2 + 1/c^2); this cell is a cube.
    r_wall = diffusion(T, n_am) * math.pi ** 2 * 3.0 / L ** 2
    q = q_slow(P)
    r_sd = r_sd_n2 + r_sd_self
    inv_t1 = r_sd / q + r_wall
    # eq. 4.14: the low-polarisation, large-field limit, q_SE = 3(2I+1)^2/(2I(2I-1))
    q_se = 3 * (2 * I_NUC + 1) ** 2 / (2 * I_NUC * (2 * I_NUC - 1))
    inv_t2 = inv_t1 + r_se / q_se
    return {"T": T, "n_rb": n, "R_SD_N2": r_sd_n2, "R_SD_self": r_sd_self,
            "R_SD": r_sd, "R_wall": r_wall, "R_SE": r_se, "q": q, "q_SE": q_se,
            "inv_T1": inv_t1, "inv_T2": inv_t2,
            "T1": 1 / inv_t1, "T2": 1 / inv_t2}


def optimum_amagat(T: float, L: float = L_CELL, P: float = 1.0) -> tuple[float, float]:
    """Where wall loss and buffer-gas spin destruction trade off.

    More gas slows diffusion to the wall as 1/n and adds spin-destruction
    collisions as n, so the sum has a minimum. Seltzer draws this for potassium
    in helium (his figure 2.23) and says the optimum is about 1 amg; this same
    code reproduces that, which is the check that it is right.
    """
    a = AMG * SIG_SD_N2 * v_rel(T, M_RB, M_N2) / q_slow(P)      # per amagat
    b = D0_N2 * math.sqrt(T / 273.15) * math.pi ** 2 * 3.0 / L ** 2   # times 1/amagat
    n_opt = math.sqrt(b / a)
    return n_opt, a * n_opt + b / n_opt


def seltzer_figure_223() -> dict:
    """Reproduce the thesis's own worked example, as a check on all of the above.

    39K in helium at 373 K, spherical cell of radius 2.5 cm. Seltzer: "In this
    case the optimal pressure is about 1 amg."
    """
    m_k, m_he = 38.9637064864 * U, 4.002602 * U
    sig, d0, R, T = 8.0e-25 * 1e-4, 0.35 * 1e-4, 2.5e-2, 373.15
    out = {}
    for q in (4.0, 6.0):
        a = AMG * sig * v_rel(T, m_k, m_he) / q
        b = d0 * math.sqrt(T / 273.15) * (math.pi / R) ** 2
        n = math.sqrt(b / a)
        out[f"q={q:g}"] = {"optimum_amg": round(n, 3),
                           "inv_T1": round(a * n + b / n, 3),
                           "linewidth_Hz": round((a * n + b / n) / (2 * math.pi), 3)}
    return out


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


def fig_budget(temps: list[float]) -> str:
    """Where the relaxation actually comes from, and how far 170 was out."""
    W, H = 760, 414
    L, R, TOP, BOT = 96, 618, 62, 320
    ymax = 200.0
    sx = lambda t: L + (R - L) * (t - temps[0]) / (temps[-1] - temps[0])
    sy = lambda v: BOT - (BOT - TOP) * v / ymax
    b = ['<text x="16" y="22" class="xs">WHERE THE GROUND-STATE RELAXATION COMES FROM</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">650 Torr N₂, 5.5 mm CELL</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0, 50, 100, 150, 200)],
          [(f"{t:g}", sx(t)) for t in (80, 100, 120, 140, 160)],
          "rate / s⁻¹", "cell temperature / °C")
    series = [("R_SD(N₂)/q", lambda d: d["R_SD_N2"] / d["q"], "m"),
              ("R_wall", lambda d: d["R_wall"], "m"),
              ("R_SD(Rb–Rb)/q", lambda d: d["R_SD_self"] / d["q"], "m"),
              ("1/T₁ = 합", lambda d: d["inv_T1"], "l")]
    rows = [rates(t + 273.15) for t in temps]
    for name, f, cls in series:
        pts = " ".join(f"{sx(t):.1f},{sy(f(d)):.1f}" for t, d in zip(temps, rows))
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
    # Rb-Rb overtakes the wall term right at the edge of the frame, so the two
    # curves end 0.7 s^-1 apart while their labels need 14px. Push the labels
    # apart and draw a leader back to each curve.
    floor_y = TOP
    for name, f, cls in sorted(series, key=lambda s: -s[1](rows[-1])):
        cy = sy(f(rows[-1]))
        y = max(cy + 3, floor_y)
        floor_y = y + 14
        if abs(y - 3 - cy) > 1:
            b.append(f'<line x1="{R}" y1="{cy:.1f}" x2="{R+16}" y2="{y-4:.1f}" class="dash"/>')
        b.append(f'<text x="{R+20}" y="{y:.1f}" class="xs">{name}</text>')
    b.append(f'<line x1="{L}" y1="{sy(170):.1f}" x2="{R}" y2="{sy(170):.1f}" class="thin"/>')
    b.append(f'<text x="{L+8}" y="{sy(170)-6:.1f}" class="xs">'
             f'Γ_g = 170 s⁻¹ — T/03부터 T/07까지 가정한 값</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">단면적은 전부 Seltzer 논문 표 A.2의 루비듐 열입니다. 자유 인자는 없고, 이 셀의 기하와 충전 밀도만 들어갑니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">지배적인 것은 N₂와의 스핀 파괴이고, 벽 확산이 그 다음입니다. Rb–Rb는 150 °C가 넘어서야 끼어듭니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">가정했던 170은 실제의 두세 배입니다. 그만큼 펌핑은 여태 적어둔 것보다 쉽습니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Ground-state relaxation budget",
        "Contributions to the ground-state relaxation rate against cell temperature: "
        "spin destruction by nitrogen, wall diffusion, and rubidium-rubidium collisions, "
        "summing to about 60 per second where 170 had been assumed.", ("bgt", "bgd"))


def fig_optimum(T: float) -> str:
    """The buffer-gas pressure trade-off, and where this cell sits on it."""
    W, H = 760, 414
    L, R, TOP, BOT = 96, 650, 62, 320
    nmin, nmax, ymax = 0.05, 3.0, 200.0
    sx = lambda n: L + (R - L) * (n - nmin) / (nmax - nmin)
    sy = lambda v: BOT - (BOT - TOP) * min(v, ymax) / ymax
    a = AMG * SIG_SD_N2 * v_rel(T, M_RB, M_N2) / q_slow(1.0)
    bb = D0_N2 * math.sqrt(T / 273.15) * math.pi ** 2 * 3.0 / L_CELL ** 2
    b = ['<text x="16" y="22" class="xs">HOW MUCH NITROGEN — THE TRADE-OFF</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">{T-273.15:.0f} °C, 5.5 mm CELL</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0, 50, 100, 150, 200)],
          [(f"{n:g}", sx(n)) for n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)],
          "1/T₁ / s⁻¹", "N₂ 충전 밀도 / amagat")
    N = 400
    ns = [nmin + (nmax - nmin) * k / N for k in range(N + 1)]
    for f, cls in ((lambda n: a * n, "m"), (lambda n: bb / n, "m"),
                   (lambda n: a * n + bb / n, "l")):
        pts = " ".join(f"{sx(n):.1f},{sy(f(n)):.1f}" for n in ns if f(n) <= ymax)
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
    n_opt, r_opt = optimum_amagat(T)
    b.append(f'<circle cx="{sx(n_opt):.1f}" cy="{sy(r_opt):.1f}" r="4" fill="var(--t0,#0d0d0d)"/>')
    b.append(f'<line x1="{sx(N_AM):.1f}" y1="{TOP}" x2="{sx(N_AM):.1f}" y2="{BOT}" class="dash"/>')
    this = a * N_AM + bb / N_AM
    b.append(f'<text x="{sx(1.55):.0f}" y="{sy(a*1.55)-7:.0f}" class="xs">N₂와의 스핀 파괴 ∝ n</text>')
    b.append(f'<text x="{sx(1.45):.0f}" y="{sy(bb/1.45)-8:.0f}" class="xs">벽으로의 확산 ∝ 1/n</text>')
    b.append(f'<text x="{sx(n_opt):.0f}" y="{sy(r_opt)+20:.0f}" class="xs" text-anchor="middle">'
             f'최적 {n_opt:.2f} amg</text>')
    b.append(f'<text x="{sx(N_AM)+6:.0f}" y="{TOP+12:.0f}" class="xs">'
             f'이 셀 {N_AM:.3f} amg (650 Torr)</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">완충기체를 더 넣으면 벽까지 가는 데 오래 걸리지만 N₂와 부딪히는 횟수가 늘어납니다. 그 둘이 만나는 곳이 최소입니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">이 셀은 {N_AM:.3f} amg, 최적은 {n_opt:.2f} amg. 완화율 차이는 {abs(this-r_opt)/r_opt*100:.1f}%입니다 — 사실상 최적점에 있습니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">같은 코드로 Seltzer 그림 2.23(He 속 ³⁹K, 반지름 2.5 cm 구형 셀)을 계산하면 0.90–1.10 amg가 나옵니다. 본인이 적은 값은 "약 1 amg"입니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Optimum buffer gas pressure",
        "Wall diffusion falls as one over density while nitrogen spin destruction rises "
        "linearly with it, so the total relaxation rate has a minimum. This cell's 650 Torr "
        "fill sits essentially on that minimum.", ("opt", "opd"))


def fig_t1t2(temps: list[float]) -> str:
    """T1 and T2 are not the same number, and at 150 C they differ by 130x."""
    W, H = 760, 414
    L, R, TOP, BOT = 100, 640, 62, 320
    sx = lambda t: L + (R - L) * (t - temps[0]) / (temps[-1] - temps[0])
    sy = lambda v: BOT - (BOT - TOP) * (math.log10(max(v, 1e-2)) + 2) / 4.0
    b = ['<text x="16" y="22" class="xs">T₁ AND T₂ ARE NOT THE SAME NUMBER</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">LOG SCALE, 0.5 G</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0.01, 0.1, 1, 10, 100)],
          [(f"{t:g}", sx(t)) for t in (80, 100, 120, 140, 160)],
          "시간 / ms", "cell temperature / °C")
    rows = [rates(t + 273.15) for t in temps]
    for key, cls, lab in (("T1", "m", "T₁ — 세로 완화"), ("T2", "l", "T₂ — 스핀 교환이 지배")):
        pts = " ".join(f"{sx(t):.1f},{sy(d[key]*1e3):.1f}" for t, d in zip(temps, rows))
        b.append(f'<polyline class="{cls}" points="{pts}"/>')
        b.append(f'<text x="{R+6}" y="{sy(rows[-1][key]*1e3)+3:.1f}" class="xs">{lab}</text>')
    b.append(f'<line x1="{L}" y1="{sy(5.88):.1f}" x2="{R}" y2="{sy(5.88):.1f}" class="thin"/>')
    b.append(f'<text x="{L+8}" y="{sy(5.88)-6:.1f}" class="xs">T/07이 쓴 T₂ = 5.88 ms (= 1/170)</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">T/07은 Γ_g가 세로 이완률인데 그것을 T₂로 썼습니다 — T₁ = T₂를 가정한 것입니다. Seltzer 식 2.135는 그렇지 않다고 말합니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">Rb–Rb 스핀 교환이 T₂를 따로 갉아먹고, 그 속도는 증기 밀도를 따라 지수적으로 커집니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">100 °C에서 T₁ 16.4 ms에 T₂ 1.49 ms, 150 °C에서는 12.2 ms에 0.09 ms. 뜨거울수록 신호는 세지고 선은 넓어집니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Longitudinal and transverse lifetimes",
        "Longitudinal and transverse spin lifetimes against cell temperature on a log scale. "
        "They are comparable at eighty degrees and differ by more than a hundredfold at a "
        "hundred and fifty, because spin exchange broadens only the transverse component.",
        ("ttt", "ttd"))


def fig_q(measured: dict) -> str:
    """The slowing-down factor, with T/05's independently measured points on it."""
    W, H = 760, 400
    L, R, TOP, BOT = 100, 620, 62, 310
    sx = lambda p: L + (R - L) * p
    sy = lambda q: BOT - (BOT - TOP) * (q - 3.5) / 7.0
    b = ['<text x="16" y="22" class="xs">n_cycle WAS NEVER A FREE PARAMETER</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">NUCLEAR SLOWING-DOWN FACTOR, I = 3/2</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{q:g}", sy(q)) for q in (4, 6, 8, 10)],
          [(f"{p:g}", sx(p)) for p in (0, 0.25, 0.5, 0.75, 1.0)],
          "q", "spin polarisation P")
    pts = " ".join(f"{sx(k/200):.1f},{sy(q_slow(k/200)):.1f}" for k in range(201))
    b.append(f'<polyline class="l" points="{pts}"/>')
    b.append(f'<line x1="{L}" y1="{sy(10):.1f}" x2="{R}" y2="{sy(10):.1f}" class="thin"/>')
    b.append(f'<text x="{L+8}" y="{sy(10)-6:.1f}" class="xs">'
             f'T/04이 모델 입력으로 넣은 n_cycle = 10</text>')
    # T/05's number is an average over the whole pumping trajectory, from P = 1/8
    # up to P ~ 0.98, so it does not belong at any single polarisation. Drawing it
    # as points at chosen x would be an illustrative placement passed off as data;
    # it goes in as a band across the axis instead.
    lo, hi = min(measured.values()), max(measured.values())
    b.append(f'<rect x="{L}" y="{sy(hi):.1f}" width="{R-L}" '
             f'height="{sy(lo)-sy(hi):.1f}" fill="var(--t2,#8a8a8a)" opacity="0.45"/>')
    b.append(f'<text x="{sx(0.30):.0f}" y="{sy(lo)+13:.0f}" class="xs">'
             f'T/05가 독립적으로 잰 값 {lo:.2f} – {hi:.2f} (펌핑 전 구간 평균)</text>')
    b.append(f'<text x="{sx(0.05):.0f}" y="{sy(5.94)-8:.0f}" class="xs">q = 6 (편광 없음)</text>')
    b.append(f'<text x="{R-6:.0f}" y="{sy(4.0)+16:.0f}" class="xs" text-anchor="end">q = 2I+1 = 4 (완전 편광)</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">핵이 붙들고 있는 각운동량 때문에 전자 스핀 하나를 뒤집으려면 광자 몇 개가 듭니다. 그 개수가 q이고, Seltzer 표 2.5에 있습니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">T/04은 이것을 10이라는 맞춰진 상수로 들고 있었습니다. T/05는 준위별로 풀어서 5.6~5.8을 얻었지만 그것이 무엇인지는 몰랐습니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">같은 수입니다. 가정도 맞춤도 아니라 표에 적혀 있는 값이고, 이 사이트의 두 계산이 서로 모르는 채로 그것을 재현했습니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "The nuclear slowing-down factor",
        "The slowing-down factor against spin polarisation, falling from six to four. The "
        "value T/05 measured independently lands on the curve; the value T/04 assumed, ten, "
        "is off the top of it.", ("qst", "qsd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    TEMPS = [80 + 2 * k for k in range(41)]                # 80 .. 160
    KEY = (80, 100, 120, 150)
    dm = json.loads((ROOT / "analysis" / "density-matrix.json").read_text())
    measured = {k: v for k, v in dm["n_cycle_matching_T04"].items()}

    n_opt, r_opt = optimum_amagat(373.15)
    here = rates(373.15)
    # The Rb-Rb term is independent of how much nitrogen is in the cell, so it
    # is the same constant at any fill and must be left out of both sides of the
    # comparison. Including it on one side only made the penalty look 5x worse.
    here_np = here["inv_T1"] - here["R_SD_self"] / here["q"]

    payload = {
        "sources": {
            "cross_sections": ("Seltzer, Developments in Alkali-Metal Atomic Magnetometry, "
                               "PhD thesis, Princeton 2008, Table A.2, rubidium column"),
            "sigma_SD_N2_cm2": 1e-22, "sigma_SD_self_cm2": 1.6e-17,
            "sigma_SE_self_cm2": 1.9e-14, "sigma_Q_N2_cm2": 5.8e-15,
            "D0_N2_cm2_s": 0.19,
            "equations": "Seltzer eqs. 2.130-2.135, 2.146-2.151, 4.14; Table 2.5",
            "geometry_note": ("Interior taken as a 5.5 mm cube: W/01 gives a 7.5 mm outer "
                              "cube and T/03 a 5.5 mm active path, which implies ~1 mm walls. "
                              "INFERRED, not measured.")},
        "cell": {"n_amagat": N_AM, "fill_Torr_at_293K": 650, "L_m": L_CELL},
        "by_temperature": {
            str(t): {k: round(v, 4) for k, v in rates(t + 273.15).items()} for t in KEY},
        "gamma_g": {
            "assumed_since_T03": 170.0,
            "computed": {str(t): round(rates(t + 273.15)["inv_T1"], 1) for t in KEY},
            "note": "2 to 3 times smaller than the value carried through T/03-T/07"},
        "T1_T2_ms": {str(t): {"T1": round(rates(t + 273.15)["T1"] * 1e3, 3),
                              "T2": round(rates(t + 273.15)["T2"] * 1e3, 4)} for t in KEY},
        "T07_assumed_T2_ms": 1e3 / 170.0,
        "slowing_down_factor": {
            "q_unpolarised": round(q_slow(0.0), 3), "q_full": round(q_slow(1.0), 3),
            "T04_assumed_n_cycle": 10.0,
            "T05_measured_independently": measured,
            "note": ("T/04's n_cycle is the nuclear slowing-down factor of Seltzer table 2.5. "
                     "T/05 solved the eight sublevels and measured 5.58-5.77 without knowing "
                     "what it was; the table says 6 unpolarised falling to 4 fully polarised.")},
        "optimum_buffer_gas": {
            "at_100C_amagat": round(n_opt, 4),
            "at_100C_fill_Torr_at_293K": round(n_opt * 760 * 293.15 / 273.15, 1),
            "inv_T1_at_optimum": round(r_opt, 2),
            "inv_T1_at_optimum_excl_self": round(r_opt, 2),
            "inv_T1_this_cell_excl_self": round(here_np, 2),
            "penalty_percent": round(abs(here_np - r_opt) / r_opt * 100, 2),
            "penalty_note": ("Rb-Rb spin destruction does not depend on the nitrogen fill, "
                             "so it is excluded from both sides. Including it would only "
                             "dilute the fraction.")},
        "check_against_thesis_figure_2_23": seltzer_figure_223(),
        "quenching": {
            "sigma_cm2": 5.8e-15,
            "R_Q_per_s_at_100C": round(
                N_AM * AMG * SIG_Q_N2 * v_rel(373.15, M_RB, M_N2), 4),
            "note": ("Seltzer eq. 2.59. Compare with the 5.75 MHz natural width: quenching "
                     "is faster than radiative decay by a wide margin, which is what T/03 "
                     "assumed when it called the excited state quenching-dominated.")},
    }
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-relax-budget.svg": fig_budget(TEMPS),
        OUT_SVG / "rb87-relax-optimum.svg": fig_optimum(373.15),
        OUT_SVG / "rb87-relax-t1t2.svg": fig_t1t2(TEMPS),
        OUT_SVG / "rb87-relax-q.svg": fig_q({k: float(v) for k, v in measured.items()}),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    for t in KEY:
        d = rates(t + 273.15)
        print(f"  {t:>3} C  1/T1 {d['inv_T1']:6.1f}/s   T1 {d['T1']*1e3:6.2f} ms   "
              f"T2 {d['T2']*1e3:7.3f} ms   R_SE {d['R_SE']:9.0f}/s")
    print(f"  assumed since T/03: 170 /s")
    print(f"  optimum N2 at 100 C: {n_opt:.3f} amg, this cell {N_AM:.3f} amg, "
          f"penalty {payload['optimum_buffer_gas']['penalty_percent']:.2f}%")
    print(f"  quenching rate {payload['quenching']['R_Q_per_s_at_100C']:.3e} /s "
          f"vs natural decay {2*math.pi*5.75e6:.3e} /s")
    print(f"  thesis fig 2.23 reproduced: {seltzer_figure_223()}")
    print(f"  q: {q_slow(0.0):.2f} -> {q_slow(1.0):.2f};  T/04 assumed 10; "
          f"T/05 measured {min(map(float, measured.values())):.2f}-"
          f"{max(map(float, measured.values())):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
