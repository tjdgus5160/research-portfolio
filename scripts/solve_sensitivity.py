#!/usr/bin/env python3
"""What the magnetometer can actually resolve, and at what temperature.

T/09 computed the signal. T/08 computed how fast it dies. Neither computed
noise, so neither could say how well the field is known. This puts the three
together and the answer is not where the rest of this repository has been
operating.

The field comes from a frequency, so the question is how well a frequency can
be read off one decaying sinusoid. That has a standard answer -- the Cramer-Rao
lower bound -- and Hunter's FID paper states it explicitly together with enough
measured parameters to check an implementation against.

    sigma_omega^2 >= 24 C / [ (A/sigma)^2 N T_r^2 ]        Hunter eq. 4
    C = (N^3/12) (1-z^2)^3 (1-z^2N) / [ ... ],  z = exp(-g2/fs)   Hunter eq. 5
    rho_B = sigma_B sqrt(2T)                               Hunter eq. 7

Two quantum noise floors feed it, both from Seltzer section 2.8:

    d<theta>_rms = sqrt(1/(2 Phi))        photon shot noise    eq. 2.164
    d<Fx>_rms    = sqrt(2 Fz T2 / N)      spin projection      eq. 2.159

The competition that sets the operating temperature: the rotation amplitude
grows with vapour density, but spin exchange shortens T2 at the same time, and
the bound degrades as g2^(3/2) against a signal that only grows as n.

    python3 scripts/solve_sensitivity.py [--check]
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "assets" / "diagrams"
OUT_JSON = ROOT / "analysis" / "sensitivity.json"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# T/08 for the lifetimes, T/09 for the rotation. Imported rather than restated,
# so a correction in either lands here without anything being retyped.
REL = _load("solve_relaxation")
FAR = _load("solve_faraday")

H = 6.62607015e-34
C_LIGHT = 299792458.0
GYRO_HZ_PER_NT = 6.99583                 # T/07, |g_F| mu_B / h for F = 2
GYRO_RAD_PER_T = 2 * math.pi * GYRO_HZ_PER_NT * 1e9

F_SAMPLE = 2.0e6                         # INFERRED, see the entry
PROBE_UW = 50.0                          # INFERRED, see the entry
BORE_M = 3.0e-3                          # W/01, the optical bore through each mount
P_X_AFTER_TIP = 0.983                    # T/07: <F_x> after a pi/2 tip, over F = 2
# Dead time before each readout. T/04 reaches 0.92 at 10 mW/cm^2 in a millisecond,
# so a millisecond of pumping is the round number that calculation supports.
T_PUMP = 1.0e-3
VOLUME = math.pi * (BORE_M / 2) ** 2 * FAR.L_CELL


def decay_correction(N: int, z: float) -> float:
    """Hunter eq. 5. How much the exponential decay costs the frequency estimate."""
    z2, z2N = z * z, z ** (2 * N)
    num = (1 - z2) ** 3 * (1 - z2N)
    den = z2 * (1 - z2N) ** 2 - N * N * z2N * (1 - z2) ** 2
    return (N ** 3 / 12.0) * num / den


def crlb_field(A_over_sigma: float, gamma2: float, T_r: float,
               gyro_Hz_per_nT: float, T_cycle: float | None = None,
               f_s: float = F_SAMPLE) -> dict:
    """Hunter eqs. 4 and 7, in tesla and tesla per root hertz.

    T_r is how long the decaying signal is watched. T_cycle is how often a new
    field estimate arrives, which is longer because the atoms have to be pumped
    again first. Eq. 7 wants the second: a noise density is per unit time, and
    time spent pumping is time not spent measuring. Hunter's own numbers make
    this explicit -- the trace in their figure 7(a) runs 0.6 ms, and they quote
    the bound "for a measurement time T = 1 ms".

    Passing T_cycle = T_r would quietly assume the pump is free.
    """
    if T_cycle is None:
        T_cycle = T_r
    N = int(f_s * T_r)
    z = math.exp(-gamma2 / f_s)
    var_omega = 24.0 / ((A_over_sigma ** 2) * N * T_r * T_r) * decay_correction(N, z)
    sigma_f = math.sqrt(var_omega) / (2 * math.pi)
    sigma_B = sigma_f / gyro_Hz_per_nT * 1e-9
    return {"sigma_B_T": sigma_B, "rho_B_T_rtHz": sigma_B * math.sqrt(2 * T_cycle),
            "N": N, "C": decay_correction(N, z)}


def shot_noise_angle(probe_uW: float, f_s: float = F_SAMPLE) -> float:
    """Per-sample angle noise from the probe's photon statistics.

    Seltzer eq. 2.164 gives the spectral density, sqrt(1/(2 Phi)) per root hertz.
    Sampling at f_s admits a bandwidth f_s/2, so one sample carries
    sigma^2 = f_s/(4 Phi). Checked against Hunter: their 50 urad at 2 MHz implies
    44 uW of probe light, which is the right order for that experiment.
    """
    flux = probe_uW * 1e-6 / (H * C_LIGHT / FAR.LAM_D2)
    return math.sqrt(f_s / (4 * flux))


def spin_projection_field(T_c: float) -> float:
    """Seltzer eq. 2.159, carried through to a field.

    An uncertainty d<Fx> in the transverse spin is read as a precession angle
    error d<Fx>/Fz after a time T2, so dB = d<Fx> / (Fz gamma T2). Substituting
    eq. 2.159 leaves dB = sqrt(2/(Fz N T2)) / gamma -- which goes as 1/sqrt(N T2),
    and once spin exchange dominates N T2 stops depending on temperature at all.
    """
    T = T_c + 273.15
    T2 = REL.rates(T)["T2"]
    N = FAR.n_rb87(T) * VOLUME
    Fz = 2.0
    return math.sqrt(2.0 / (Fz * N * T2)) / GYRO_RAD_PER_T


def sensitivity(T_c: float, probe_uW: float = PROBE_UW) -> dict:
    """Everything at one cell temperature."""
    T = T_c + 273.15
    T2 = REL.rates(T)["T2"]
    gamma2 = 1.0 / T2
    n = FAR.n_rb87(T)
    best = FAR.best_detuning(n)
    amplitude = abs(best["signal_rad"]) * P_X_AFTER_TIP
    sigma = shot_noise_angle(probe_uW)
    T_r = 2.0 * T2                        # Hunter: the window that minimises the bound
    cr = crlb_field(amplitude / sigma, gamma2, T_r, GYRO_HZ_PER_NT,
                    T_cycle=T_r + T_PUMP)
    return {"T_c": T_c, "T2_s": T2, "n87_m3": n, "window_cycle_s": T_r + T_PUMP,
            "detuning_GHz": best["detuning_Hz"] / 1e9,
            "amplitude_rad": amplitude, "sigma_theta_rad": sigma,
            "snr": amplitude / sigma, "window_s": T_r,
            "rho_photon_T": cr["rho_B_T_rtHz"],
            "rho_spin_T": spin_projection_field(T_c)}


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


def fig_vs_T(temps: list[float], best: dict) -> str:
    W, H = 760, 414
    L, R, TOP, BOT = 104, 636, 62, 316
    sx = lambda t: L + (R - L) * (t - temps[0]) / (temps[-1] - temps[0])
    sy = lambda v: BOT - (BOT - TOP) * (math.log10(max(v, 1e-15)) + 15) / 3.0
    b = ['<text x="16" y="22" class="xs">WHERE TO RUN THE CELL</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">{PROBE_UW:g} µW 프로브, 1 ms 펌프</text>']
    _axes(b, L, R, TOP, BOT,
          [(lab, sy(v)) for lab, v in (("1 fT", 1e-15), ("10 fT", 1e-14),
                                       ("100 fT", 1e-13), ("1 pT", 1e-12))],
          [(f"{t:g}", sx(t)) for t in (60, 80, 100, 120, 140)],
          "잡음 밀도 / T·Hz^(−1/2)", "cell temperature / °C")
    rows = [sensitivity(t) for t in temps]
    b.append('<polyline class="l" points="'
             + " ".join(f"{sx(t):.1f},{sy(r['rho_photon_T']):.1f}" for t, r in zip(temps, rows)) + '"/>')
    b.append('<polyline class="m" points="'
             + " ".join(f"{sx(t):.1f},{sy(r['rho_spin_T']):.1f}" for t, r in zip(temps, rows)) + '"/>')
    b.append(f'<circle cx="{sx(best["T_c"]):.1f}" cy="{sy(best["rho_photon_T"]):.1f}" '
             f'r="4" fill="var(--t0,#0d0d0d)"/>')
    b.append(f'<text x="{sx(best["T_c"]):.0f}" y="{sy(best["rho_photon_T"])-12:.0f}" '
             f'class="xs" text-anchor="middle">{best["T_c"]:.0f} °C — {best["rho_photon_T"]*1e15:.0f} fT/√Hz</text>')
    b.append(f'<text x="{sx(128):.0f}" y="{sy(rows[-1]["rho_photon_T"])-10:.0f}" class="xs">'
             f'광자 산탄 잡음 한계</text>')
    b.append(f'<text x="{sx(96):.0f}" y="{sy(rows[0]["rho_spin_T"])-9:.0f}" class="xs">'
             f'스핀 투영 잡음 — 원자 자체의 한계</text>')
    for t in (100, 120, 150):
        if t <= temps[-1]:
            b.append(f'<line x1="{sx(t):.0f}" y1="{BOT}" x2="{sx(t):.0f}" y2="{BOT-9}" class="thin"/>')
    b.append(f'<text x="16" y="{H-38}" class="xs">차가우면 원자가 모자라 신호가 작고, 뜨거우면 스핀 교환이 T₂를 먼저 죽입니다. 그 사이에 최소가 있습니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">최적은 {best["T_c"]:.0f} °C입니다 — T/03부터 T/06까지가 예로 들어온 100~150 °C보다 한참 아래입니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">두 곡선이 20배 넘게 벌어져 있습니다. 이 셀은 원자가 아니라 광자에 막혀 있고, 그래서 프로브 출력이 아직 이깁니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "Noise density against cell temperature",
        "Photon shot noise and spin projection noise against cell temperature on a log scale. "
        "The photon-limited curve has a minimum near eighty degrees; the spin projection floor "
        "is more than twenty times lower and almost flat.", ("svt", "svd"))


def fig_window(T_c: float) -> str:
    W, H = 760, 400
    L, R, TOP, BOT = 104, 640, 62, 302
    T = T_c + 273.15
    T2 = REL.rates(T)["T2"]
    n = FAR.n_rb87(T)
    A = abs(FAR.best_detuning(n)["signal_rad"]) * P_X_AFTER_TIP
    sig = shot_noise_angle(PROBE_UW)
    sx = lambda k: L + (R - L) * (k - 0.2) / 5.8
    sy = lambda v: BOT - (BOT - TOP) * (v * 1e15 - 30) / 45.0
    b = ['<text x="16" y="22" class="xs">HOW LONG TO WATCH ONE DECAY</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">{T_c:.0f} °C, T₂ = {T2*1e3:.2f} ms</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v * 1e-15)) for v in (30, 45, 60, 75)],
          [(f"{k:g}", sx(k)) for k in (1, 2, 3, 4, 5, 6)],
          "잡음 밀도 / fT·Hz^(−1/2)", "관측 창 / T₂")
    for cyc, cls in ((False, "m"), (True, "l")):
        # Below about half a coherence time the bound blows up and the curve
        # would run off the top of the frame; drop those points rather than draw
        # outside the axes.
        pts = []
        for i in range(4, 121):
            k = i * 0.05
            Tr = k * T2
            r = crlb_field(A / sig, 1 / T2, Tr, GYRO_HZ_PER_NT,
                           T_cycle=Tr + T_PUMP if cyc else None)["rho_B_T_rtHz"]
            if r * 1e15 > 75.0:
                pts = []                 # restart once it comes back into range
                continue
            pts.append(f"{sx(k):.1f},{sy(r):.1f}")
        b.append(f'<polyline class="{cls}" points="{" ".join(pts)}"/>')
    b.append(f'<line x1="{sx(2):.0f}" y1="{TOP}" x2="{sx(2):.0f}" y2="{BOT}" class="dash"/>')
    b.append(f'<text x="{sx(2)+6:.0f}" y="{TOP+12}" class="xs">'
             f'2 × T₂ — Hunter가 적은 최적 창</text>')
    b.append(f'<text x="{sx(4.3):.0f}" y="{sy(52e-15):.0f}" class="xs">펌프 시간을 포함</text>')
    b.append(f'<text x="{sx(4.3):.0f}" y="{sy(46e-15):.0f}" class="xs">관측 시간만</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">더 오래 보면 데이터가 늘지만 신호가 이미 죽어 있어 새 정보가 없고, 다음 측정이 그만큼 늦어집니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">펌프 없이 계산하면 최소가 정확히 2·T₂에 떨어집니다 — 논문이 적은 값 그대로입니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">1 ms 펌프를 넣으면 2.2·T₂로 조금 밀리고, 2·T₂를 그대로 써도 손해는 보이지 않습니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "The optimum readout window",
        "Noise density against how long each decay is watched, with and without the pump dead "
        "time counted. The minimum falls at twice the coherence time, which is the rule the "
        "source states.", ("wnt", "wnd"))


def fig_mechanism(temps: list[float], best_T: float) -> str:
    W, H = 760, 400
    L, R, TOP, BOT = 104, 630, 62, 302
    sx = lambda t: L + (R - L) * (t - temps[0]) / (temps[-1] - temps[0])
    sy = lambda v: BOT - (BOT - TOP) * (math.log10(max(v, 1e-3)) + 1) / 3.6
    ref = sensitivity(temps[0])
    b = ['<text x="16" y="22" class="xs">WHY THERE IS AN OPTIMUM AT ALL</text>',
         f'<text x="{W-16}" y="22" class="xs" text-anchor="end">{temps[0]:g} °C에서 1로 규격화</text>']
    _axes(b, L, R, TOP, BOT,
          [(f"{v:g}", sy(v)) for v in (0.1, 1, 10, 100)],
          [(f"{t:g}", sx(t)) for t in (60, 80, 100, 120, 140)],
          "상대값", "cell temperature / °C")
    rows = [sensitivity(t) for t in temps]
    series = [("신호 진폭 ∝ n", [r["amplitude_rad"] / ref["amplitude_rad"] for r in rows], "m"),
              ("γ₂^(3/2)", [(ref["T2_s"] / r["T2_s"]) ** 1.5 for r in rows], "m"),
              ("잡음 밀도 = 둘의 비", [r["rho_photon_T"] / ref["rho_photon_T"] for r in rows], "l")]
    for name, vals, cls in series:
        b.append(f'<polyline class="{cls}" points="'
                 + " ".join(f"{sx(t):.1f},{sy(v):.1f}" for t, v in zip(temps, vals)) + '"/>')
        b.append(f'<text x="{R+5}" y="{sy(vals[-1])+3:.1f}" class="xs">{name}</text>')
    b.append(f'<text x="16" y="{H-38}" class="xs">회전 진폭은 증기 밀도를 따라 자랍니다. 주파수를 읽는 정밀도는 감쇠율의 3/2제곱으로 나빠집니다.</text>')
    b.append(f'<text x="16" y="{H-24}" class="xs">γ₂ = a + bn이라 낮은 온도에서는 a가 지배해 신호만 자라고, 높은 온도에서는 bn이 지배해 n^(1/2)로 나빠집니다.</text>')
    b.append(f'<text x="16" y="{H-10}" class="xs">해석적으로는 bn = 2a인 곳(약 77 °C)이 최소입니다. 실제로 {best_T:.0f} °C인 것은 최적 detuning이 함께 움직여 진폭이 n보다 빨리 자라기 때문입니다.</text>')
    return svg_wrap(W, H, "\n".join(b), "The competition that sets the temperature",
        "Signal amplitude and the three-halves power of the decay rate against temperature, and "
        "their ratio. The first grows with vapour density, the second grows faster once spin "
        "exchange takes over, and the ratio has a minimum between them.", ("mct", "mcd"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    temps = [60 + k for k in range(81)]                 # 60 .. 140
    rows = [sensitivity(t) for t in temps]
    best = min(rows, key=lambda r: r["rho_photon_T"])

    # Reproduce the published bound from the paper the formula came from.
    hunter = crlb_field(20e-3 / 50e-6, 1.5e3, 0.6e-3, 3.4986, T_cycle=1.0e-3)

    # Is the source's rule -- watch for 2/gamma2 -- still where the minimum is?
    T2b = best["T2_s"]
    nb = FAR.n_rb87(best["T_c"] + 273.15)
    Ab = abs(FAR.best_detuning(nb)["signal_rad"]) * P_X_AFTER_TIP
    sb = shot_noise_angle(PROBE_UW)
    def at(k, dead):
        Tr = k * T2b
        return crlb_field(Ab / sb, 1 / T2b, Tr, GYRO_HZ_PER_NT,
                          T_cycle=Tr + T_PUMP if dead else None)["rho_B_T_rtHz"]
    win_free = min(((at(i * 0.05, False), i * 0.05) for i in range(4, 121)))
    win_dead = min(((at(i * 0.05, True), i * 0.05) for i in range(4, 121)))

    payload = {
        "sources": {
            "crlb": ("Hunter et al., Phys. Rev. Applied 10, 014002 (2018), eqs. 4, 5 and 7. "
                     "A caesium FID magnetometer; the bound itself is species independent."),
            "noise_floors": ("Seltzer thesis eqs. 2.159 (spin projection) and 2.164 (photon "
                             "shot). Fabricant et al. 2023 eqs. 17-18 give the same scalings."),
            "inputs": "T2 from T/08, rotation amplitude from T/09, gyromagnetic ratio from T/07."},
        "model_inputs": {
            "probe_uW": PROBE_UW, "sample_rate_Hz": F_SAMPLE,
            "pump_dead_time_s": T_PUMP, "P_x_after_tip": P_X_AFTER_TIP,
            "probe_volume_cm3": VOLUME * 1e6, "bore_m": BORE_M,
            "note": ("Probe power and sample rate are chosen, not measured -- both are "
                     "INFERRED. The sensitivity goes as the inverse square root of probe "
                     "power, and the optimum temperature does not move with it.")},
        "check_against_hunter": {
            "inputs": "A 20 mrad, sigma 50 urad, gamma2 1.5 kHz, fs 2 MHz, Tr 0.6 ms, T 1 ms",
            "computed_pT_rtHz": round(hunter["rho_B_T_rtHz"] * 1e12, 2),
            "published_pT_rtHz": 2.0},
        "optimum": {
            "T_c": best["T_c"],
            "rho_photon_fT_rtHz": round(best["rho_photon_T"] * 1e15, 1),
            "rho_spin_fT_rtHz": round(best["rho_spin_T"] * 1e15, 2),
            "T2_ms": round(best["T2_s"] * 1e3, 3),
            "snr": round(best["snr"], 0),
            "detuning_GHz": round(best["detuning_GHz"], 2),
            "cycle_ms": round(best["window_cycle_s"] * 1e3, 2)},
        "by_temperature": {
            str(r["T_c"]): {"T2_ms": round(r["T2_s"] * 1e3, 3), "snr": round(r["snr"], 0),
                            "rho_photon_fT": round(r["rho_photon_T"] * 1e15, 1),
                            "rho_spin_fT": round(r["rho_spin_T"] * 1e15, 2)}
            for r in rows if r["T_c"] % 10 == 0},
        "readout_window": {
            "source_rule": "Hunter: T_r ~ 2/gamma2",
            "found_without_dead_time": win_free[1],
            "found_with_1ms_pump": win_dead[1]},
        "probe_power_scaling": {
            str(p): round(min(sensitivity(t, p)["rho_photon_T"] for t in temps) * 1e15, 1)
            for p in (10, 50, 200)},
        "photon_vs_spin_at_optimum": round(best["rho_photon_T"] / best["rho_spin_T"], 1),
    }
    files = {
        OUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUT_SVG / "rb87-sens-temperature.svg": fig_vs_T(temps, best),
        OUT_SVG / "rb87-sens-window.svg": fig_window(best["T_c"]),
        OUT_SVG / "rb87-sens-mechanism.svg": fig_mechanism(temps, best["T_c"]),
    }
    if a.check:
        same = all(p.exists() and p.read_text() == v for p, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for p, v in files.items():
        p.write_text(v, encoding="utf-8")
    print(f"  Hunter reproduced: {hunter['rho_B_T_rtHz']*1e12:.2f} pT/rtHz "
          f"vs published >= 2")
    print(f"  window: best {win_free[1]:.2f} T2 without dead time "
          f"(source says 2), {win_dead[1]:.2f} T2 with a 1 ms pump")
    print(f"  optimum {best['T_c']:.0f} C -> {best['rho_photon_T']*1e15:.1f} fT/rtHz "
          f"photon, {best['rho_spin_T']*1e15:.2f} fT/rtHz spin "
          f"({payload['photon_vs_spin_at_optimum']:.0f}x apart)")
    for t in (60, 80, 100, 120, 140):
        r = payload["by_temperature"][str(t)]
        print(f"  {t:>3} C  T2 {r['T2_ms']:>6.2f} ms  SNR {r['snr']:>6.0f}  "
              f"photon {r['rho_photon_fT']:>6.1f} fT  spin {r['rho_spin_fT']:>5.2f} fT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
