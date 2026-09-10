#!/usr/bin/env python3
"""SUPERSEDED by scripts/validators/contrast.mjs — kept as a record, not a gate.

This inferred each element's background from its selector with regular
expressions. It was wrong in three different ways before it was replaced:

  * false positives — .skip and .btn.ghost declare their own background, which
    a selector-name guess cannot see, so their text looked invisible;
  * false negatives — .ticker-run inherits its ground from .ticker, which the
    guess also could not see, so a real 2.40:1 went unreported;
  * substring matching — ".bar-nav a:not(.btn)" contains ".btn", so it was
    filed under the dark ground twice, once before and once after a "fix".

The browser version reads what is actually painted and needs no table of
assumptions at all. It found a defect this one structurally could not: .no is
used on the light service rows and again on the dark work cards, at 1.71:1 on
the second.

Original docstring follows.

Prove the four tones are still readable in both palettes.

The palette is deliberately tiny — four tones, no more — and that makes it easy
to reach for the mid tone because it looks right, without noticing it is 2.4:1
against the light ground. Every label on this site is 8-10px pixel type, which
is exactly the case WCAG's 4.5:1 exists for.

This checks the palettes themselves and then every rule that paints text, so a
future edit cannot quietly put small copy back on a tone that fails.

    python3 scripts/validators/validate_contrast.py
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHEETS = ["styles.css", "entry.css", "decor.css"]

PALETTES = {
    "mono": {"t0": "#0d0d0d", "t1": "#3a3a3a", "t2": "#8a8a8a", "t3": "#d7d7d7"},
    "dmg":  {"t0": "#0f1a0b", "t1": "#30452a", "t2": "#6b8f5a", "t3": "#c6d8a8"},
}

# Which ground each selector actually sits on. Anything not listed is assumed to
# be on the light ground, which is the stricter assumption.
# .menu inherits the bar's light ground and .game-in sets --t3 explicitly, so
# neither is reversed — the first run of this gate is what made me check rather
# than assume, and both were in this list wrongly.
ON_DARK = (".strip", ".ticker", ".work ", ".work.", ".credit", ".brand", ".bits",
           ".foot", ".svc li:hover", ".e-views figcaption", ".stat ",
           ".btn", ".ab-b", ".start", ".d ")

# Purely decorative text — a texture, not content. WCAG does not hold decoration
# to a contrast ratio, and forcing this to 4.5:1 would defeat what it is for.
# The exemption is not taken on trust: the gate checks the markup really does
# hide each of these from assistive tech before letting it through.
DECORATIVE = {".bits": "bits"}

def lum(hexv: str) -> float:
    c = [int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a: str, b: str) -> float:
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)

def px(v: str) -> float | None:
    m = re.match(r"\s*(\d+(?:\.\d+)?)px", v)
    return float(m.group(1)) if m else None

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args()
    checks = []

    for name, p in PALETTES.items():
        # four tones that are not four distinct tones is not a palette
        seen = {}
        for k, v in p.items():
            checks.append((f"palette {name}", f"{k} is distinct from {seen.get(v, '')}",
                           v not in seen, f"{k} and {seen.get(v,'')} are both {v}"))
            seen[v] = k
        for fg, bg, need, what in (("t0", "t3", 4.5, "ink on ground"),
                                   ("t1", "t3", 4.5, "secondary on ground"),
                                   ("t3", "t0", 4.5, "reversed"),
                                   ("t2", "t0", 4.5, "secondary reversed")):
            r = ratio(p[fg], p[bg])
            checks.append((f"palette {name}", f"{fg} on {bg} ({what})",
                           r >= need, f"{r:.2f}:1, need {need}"))

    for fn in SHEETS:
        f = ROOT / fn
        if not f.exists():
            continue
        s = f.read_text(encoding="utf-8")
        for m in re.finditer(r"([^{}]+)\{([^}]*)\}", s):
            sel = m.group(1).strip().split("\n")[-1]
            body = m.group(2)
            # `color` and nothing else: border-left-color, outline-color and
            # background-color are not text, and a lookbehind for "border-"
            # does not catch "border-left-". Anchor on a property boundary.
            cm = re.search(r"(?:^|;)\s*color\s*:\s*var\(--(t[0-3])\)", body)
            if not cm:
                continue
            tone = cm.group(1)
            size = px((re.search(r"font-size\s*:\s*([^;]+)", body) or [None, ""])[1]) \
                if re.search(r"font-size\s*:\s*([^;]+)", body) else None
            # If the rule paints its own background, that is the ground —
            # reading it is exact, where guessing from the selector name is not.
            # Most of the "invisible text" this gate first reported was really
            # my guess being wrong about rules like .skip and .btn.ghost, which
            # set background and colour together.
            own = re.search(r"background(?:-color)?\s*:[^;]*var\(--(t[0-3])\)", body)
            if own:
                ground = own.group(1)
            else:
                # Substring matching put ".bar-nav a:not(.btn)" on the dark
                # ground because the selector contains ".btn". Compare whole
                # selector tokens instead.
                toks = set(re.findall(r"[.#][A-Za-z0-9_-]+", sel))
                dark = any(set(re.findall(r"[.#][A-Za-z0-9_-]+", k)) <= toks
                           for k in ON_DARK)
                ground = "t0" if dark else "t3"
            if tone == ground:
                # Text painted in its own ground colour is invisible, not
                # decorative. The first version of this gate skipped that case
                # and so passed a page whose kicker was the same colour as the
                # page — found by an independent review, not by me.
                checks.append((f"text {'both'}",
                               f"{fn} {sel[:40]} — --{tone} on its own ground",
                               False, "1.00:1, text is invisible"))
                continue
            skip = next((cls for k, cls in DECORATIVE.items() if k in sel), None)
            if skip:
                pages = [ROOT / "index.html", ROOT / "en" / "index.html"]
                hidden = all(
                    re.search(rf'class="{skip}"[^>]*aria-hidden="true"', q.read_text(encoding="utf-8"))
                    for q in pages if q.exists())
                checks.append(("decorative",
                               f"{fn} {sel[:40]} is hidden from assistive tech",
                               hidden,
                               "exempt from contrast" if hidden
                               else "claims to be decoration but is not aria-hidden"))
                if hidden:
                    continue
            need = 3.0 if (size or 0) >= 24 else 4.5
            for pname, p in PALETTES.items():
                r = ratio(p[tone], p[ground])
                checks.append((f"text {pname}",
                               f"{fn} {sel[:40]} — --{tone} on --{ground}",
                               r >= need,
                               f"{r:.2f}:1, need {need} at {size or 'inherited'}px"))

    fails = [c for c in checks if not c[2]]
    if a.as_json:
        print(json.dumps({"verdict": "PASS" if not fails else "FAIL",
                          "checks": len(checks), "failures": len(fails),
                          "failing": [{"gate": g, "check": c, "detail": d}
                                      for g, c, _, d in fails]},
                         indent=2, ensure_ascii=False))
    else:
        cur = None
        for g, c, ok, d in checks:
            if not ok:
                if g != cur:
                    print(f"\n{g}"); cur = g
                print(f"  FAIL  {c}  ({d})")
        print()
        print(f"PASS — {len(checks)} contrast checks" if not fails
              else f"FAIL — {len(fails)} of {len(checks)} contrast checks failed")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
