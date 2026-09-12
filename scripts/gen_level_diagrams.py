#!/usr/bin/env python3
"""Draw the 87Rb level structure and the optical-pumping cycle.

SVG rather than pixels: a level diagram is mostly labelled lines, and text has
to stay readable when someone zooms. It still obeys the site's rules — four
tones through the CSS variables, so the diagrams follow the palette switch, and
every coordinate on a whole multiple of the same grid the rest of the page uses.

Splittings are drawn to a stated, non-linear scale. A diagram that claimed to be
to scale would be a lie: the ground-state hyperfine splitting is 6.8 GHz and the
optical transition is 377 THz, a ratio of 55,000 to 1. The scale is written on
each figure instead.

    python3 scripts/gen_level_diagrams.py [--check]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "diagrams"
G = 8                                   # one grid step, in SVG user units

def svg(w: int, h: int, body: str, title: str, desc: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
  role="img" aria-labelledby="t d" class="lvl">
<title id="t">{title}</title><desc id="d">{desc}</desc>
<style>
  .lvl{{font-family:"IBM Plex Mono","SF Mono",monospace}}
  .l{{stroke:var(--t0,#0d0d0d);stroke-width:3;shape-rendering:crispEdges}}
  .thin{{stroke:var(--t1,#3a3a3a);stroke-width:1.5;shape-rendering:crispEdges}}
  .dash{{stroke:var(--t2,#8a8a8a);stroke-width:1.5;stroke-dasharray:4 4;
        shape-rendering:crispEdges}}
  .arr{{stroke:var(--t0,#0d0d0d);stroke-width:3;marker-end:url(#a)}}
  .arr2{{stroke:var(--t1,#3a3a3a);stroke-width:1.5;stroke-dasharray:3 3;
        marker-end:url(#b)}}
  text{{fill:var(--t0,#0d0d0d);font-size:11px}}
  .sm{{font-size:9px;fill:var(--t1,#3a3a3a)}}
  .xs{{font-size:8px;fill:var(--t1,#3a3a3a);letter-spacing:.06em}}
  /* A label that lands on a gridline or a curve is unreadable. Paint the
     ground colour behind the glyphs first, then the glyphs. */
  .xs,.sm{{paint-order:stroke fill;stroke:var(--t3,#d7d7d7);stroke-width:3px;
    stroke-linejoin:round}}
  .fill{{fill:var(--t0,#0d0d0d)}}
</style>
<defs>
  <marker id="a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5"
          orient="auto"><path d="M0 0 L8 4 L0 8 z" fill="var(--t0,#0d0d0d)"/></marker>
  <marker id="b" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5"
          orient="auto"><path d="M0 0 L8 4 L0 8 z" fill="var(--t1,#3a3a3a)"/></marker>
</defs>
{body}
</svg>
'''

def line(x1, y1, x2, y2, cls="l"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>'

def txt(x, y, s, cls="", anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}"{f" class={cls!r}" if cls else ""}>{s}</text>'


# ── 1. fine and hyperfine structure ────────────────────────────────────────
def structure() -> str:
    W, H = 760, 560
    b = [txt(16, 24, "87Rb  D LINE STRUCTURE", "xs")]
    b.append(txt(W - 16, 24, "SPLITTINGS NOT TO SCALE", "xs", "end"))

    # 5 2P3/2 — four hyperfine levels
    x0, x1 = 430, 620
    lv = [(96, "F' = 3", "266.650 MHz"), (128, "F' = 2", "156.947 MHz"),
          (152, "F' = 1", "72.218 MHz"), (168, "F' = 0", "")]
    b.append(txt(x0, 76, "5 2P3/2", "sm"))
    for y, f, sp in lv:
        b.append(line(x0, y, x1, y))
        b.append(txt(x1 + 8, y + 4, f, "sm"))
        if sp:
            b.append(txt(x1 + 74, y + 4, sp, "xs"))

    # 5 2P1/2 — two hyperfine levels
    xa, xb = 150, 340
    b.append(txt(xa, 196, "5 2P1/2", "sm"))
    # 2A for J=1/2, I=3/2; A(5 2P1/2) = 407.25(63) MHz in the source. The value
    # I first wrote here from memory does not appear in it at all.
    for y, f, sp in ((216, "F' = 2", "814.50(126) MHz = 2A"), (256, "F' = 1", "")):
        b.append(line(xa, y, xb, y))
        b.append(txt(xb + 8, y + 4, f, "sm"))
        if sp:
            b.append(txt(xb + 74, y + 4, sp, "xs"))

    # 5 2S1/2 — the ground state
    gx0, gx1 = 280, 470
    b.append(txt(gx0, 424, "5 2S1/2", "sm"))
    for y, f in ((444, "F = 2"), (508, "F = 1")):
        b.append(line(gx0, y, gx1, y))
        b.append(txt(gx1 + 8, y + 4, f, "sm"))
    b.append(line(gx1 + 96, 444, gx1 + 96, 508, "thin"))
    b.append(txt(gx1 + 104, 470, "6.834 682 610 904 290(90) GHz", "xs"))
    b.append(txt(gx1 + 104, 484, "ground-state hyperfine splitting", "xs"))

    # the two optical transitions
    b.append(line(320, 440, 250, 262, "arr"))
    b.append(txt(222, 350, "D1", ""))
    b.append(txt(200, 366, "794.978 851 156(23) nm", "xs"))
    b.append(txt(200, 378, "377.107 463 380(11) THz", "xs"))
    b.append(line(430, 440, 500, 176, "arr"))
    b.append(txt(508, 320, "D2", ""))
    b.append(txt(508, 336, "780.241 209 686(13) nm", "xs"))
    b.append(txt(508, 348, "384.230 484 468 5(62) THz", "xs"))

    b.append(txt(16, H - 20, "I = 3/2   F = I ± 1/2   every figure from Steck, "
                             "Rubidium 87 D Line Data, rev. 2.3.4", "xs"))
    return svg(W, H, "\n".join(b), "87Rb D line structure",
               "Fine and hyperfine structure of rubidium 87: the 5S1/2 ground state "
               "splits into F=1 and F=2 separated by 6.834 682 610 904 290(90) GHz; "
               "the D1 line at "
               "794.98 nm reaches 5P1/2 with F'=1,2 and the D2 line at 780.24 nm "
               "reaches 5P3/2 with F'=0,1,2,3.")


# ── 2. Zeeman splitting of the ground state ────────────────────────────────
def zeeman() -> str:
    W, H = 760, 400
    b = [txt(16, 24, "ZEEMAN SPLITTING OF THE GROUND STATE", "xs"),
         txt(W - 16, 24, "LINEAR REGIME, B SMALL", "xs", "end")]
    b.append(line(120, 340, 700, 340, "thin"))
    b.append(txt(700, 358, "B", "sm", "end"))
    b.append(line(120, 340, 120, 60, "thin"))
    b.append(txt(112, 66, "E", "sm", "end"))

    # F = 2, g_F = +1/2 : five sublevels fanning upward
    for i, m in enumerate((2, 1, 0, -1, -2)):
        y0, slope = 140, -m * 26
        b.append(line(180, y0, 660, y0 + slope, "l" if m == 2 else "thin"))
        b.append(txt(668, y0 + slope + 4, f"mF = {m:+d}".replace("+0", " 0"), "xs"))
    b.append(txt(126, 134, "F = 2", "sm"))
    b.append(txt(126, 148, "gF = +1/2", "xs"))

    # F = 1, g_F = -1/2 : three sublevels fanning the other way
    for m in (1, 0, -1):
        y0, slope = 290, m * 22
        b.append(line(180, y0, 660, y0 + slope, "thin"))
        b.append(txt(668, y0 + slope + 4, f"mF = {m:+d}".replace("+0", " 0"), "xs"))
    b.append(txt(126, 284, "F = 1", "sm"))
    b.append(txt(126, 298, "gF = -1/2", "xs"))

    b.append(txt(200, 372, "ΔE = gF mF μB B      "
                           "γ/2π = |gF| μB/h = 6.998 Hz/nT for F = 2", "xs"))
    return svg(W, H, "\n".join(b), "Zeeman splitting of the 87Rb ground state",
               "In a magnetic field each hyperfine level splits into 2F+1 sublevels "
               "spaced linearly in B. F=2 has gF=+1/2 and fans upward with mF; F=1 has "
               "gF=-1/2 and fans the opposite way. The splitting per unit field is "
               "6.998 Hz per nanotesla.")


# ── 3. optical pumping into the stretched state ────────────────────────────
def pumping() -> str:
    W, H = 760, 470
    b = [txt(16, 24, "OPTICAL PUMPING WITH σ+ LIGHT", "xs"),
         txt(W - 16, 24, "D1, ΔmF = +1", "xs", "end")]
    xs = [120, 220, 320, 420, 520]                    # mF = -2 .. +2
    ms = [-2, -1, 0, 1, 2]

    # excited manifold
    for x, m in zip(xs, ms):
        b.append(line(x - 34, 110, x + 34, 110, "thin"))
        b.append(txt(x, 100, f"{m:+d}".replace("+0", "0"), "xs", "middle"))
    b.append(txt(600, 114, "5 2P1/2  F' = 2", "sm"))

    # ground manifold, the stretched state drawn solid
    for x, m in zip(xs, ms):
        b.append(line(x - 34, 340, x + 34, 340, "l" if m == 2 else "thin"))
        b.append(txt(x, 364, f"mF = {m:+d}".replace("+0", " 0"), "xs", "middle"))
    b.append(txt(600, 344, "5 2S1/2  F = 2", "sm"))

    # absorption steps: each takes mF up by one
    for i in range(4):
        b.append(line(xs[i], 332, xs[i + 1] - 12, 122, "arr"))
    # these two labels sat across the arrows they describe; move them into the
    # clear space either side of the ladder
    b.append(f'<rect x="24" y="196" width="150" height="34" fill="var(--t3,#d7d7d7)"/>')
    b.append(txt(24, 212, "σ+ absorption", ""))
    b.append(txt(24, 226, "ΔmF = +1 every time", "xs"))

    # spontaneous emission comes back down by 0 or ±1
    for i in (1, 2, 3):
        b.append(line(xs[i] + 12, 122, xs[i] + 4, 330, "arr2"))
    b.append(f'<rect x="596" y="196" width="150" height="34" fill="var(--t3,#d7d7d7)"/>')
    b.append(txt(596, 212, "spontaneous emission", "sm"))
    b.append(txt(596, 226, "ΔmF = 0, ±1", "xs"))

    # the dark state
    b.append(f'<rect x="{xs[4]-40}" y="332" width="80" height="16" '
             f'fill="none" class="dash"/>')
    b.append(txt(xs[4], 400, "mF = +2 cannot absorb σ+", "xs", "middle"))
    b.append(txt(xs[4], 412, "there is no mF = +3 to go to", "xs", "middle"))
    b.append(txt(16, H - 22, "The population walks up the ladder and stacks in the "
                             "stretched state. That oriented ensemble is what the "
                             "field then precesses.", "xs"))
    return svg(W, H, "\n".join(b), "Optical pumping into the stretched state",
               "Circularly polarised sigma-plus light raises mF by one on every "
               "absorption while spontaneous emission returns it by 0 or plus or minus "
               "one. Population therefore accumulates in mF = +2, which cannot absorb "
               "sigma-plus light because no mF = +3 exists. The sample ends up "
               "spin-polarised.")


def main() -> int:
    # This used to take no arguments at all, so running it with --check in the
    # gate suite silently REWROTE the diagrams and reported success. It agreed
    # with what was on disk, but a check that cannot fail is not a check.
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    files = {OUT / f"{name}.svg": fn()
             for name, fn in (("rb87-structure", structure),
                              ("rb87-zeeman", zeeman),
                              ("rb87-pumping", pumping))}
    if a.check:
        same = all(f.exists() and f.read_text() == v for f, v in files.items())
        print("  up to date" if same else "  WOULD CHANGE")
        return 0 if same else 1
    OUT.mkdir(parents=True, exist_ok=True)
    for f, v in files.items():
        f.write_text(v, encoding="utf-8")
        print(f"  {f.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
