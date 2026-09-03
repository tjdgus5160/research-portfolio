#!/usr/bin/env python3
"""Deterministic gate for the portfolio site.

The design lives in tokens.css. This checks that the rest of the project
actually goes through it rather than around it, and that the markup keeps the
accessibility promises DESIGN.md makes.

It says nothing about whether the page looks good. That is a human judgement
and it happens after this passes.

    python3 scripts/validators/validate_site.py
"""

from __future__ import annotations

import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ROOT / "assets/css/tokens.css"

# Files allowed to declare raw values, because they define them.
EXEMPT = {"assets/css/tokens.css"}

HEX     = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FUNCCOL = re.compile(r"\b(?:rgb|rgba|hsl|hsla|oklch|lab)\s*\(", re.I)
FONTPX  = re.compile(r"font-size\s*:\s*[^;}]*?\d*\.?\d+px", re.I)
DURATION= re.compile(r"(?:transition|animation)(?:-duration|-delay)?\s*:\s*[^;}]*?\d*\.?\d+m?s", re.I)
VARUSE  = re.compile(r"var\(\s*(--[a-zA-Z0-9-]+)")
VARDEF  = re.compile(r"^\s*(--[a-zA-Z0-9-]+)\s*:", re.M)


class Report:
    def __init__(self): self.checks = []
    def add(self, gate, name, ok, detail=""):
        self.checks.append({"gate": gate, "check": name, "passed": bool(ok), "detail": detail})
    @property
    def failures(self): return [c for c in self.checks if not c["passed"]]
    @property
    def passed(self): return not self.failures


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def check_tokens_exist(rep):
    if not TOKENS.is_file():
        rep.add("tokens", "assets/css/tokens.css exists", False, "missing")
        return set()
    defined = set(VARDEF.findall(TOKENS.read_text()))
    rep.add("tokens", "tokens.css defines the design system", bool(defined), f"{len(defined)} tokens")
    return defined


def check_no_raw_values(rep):
    for path in sorted(ROOT.glob("assets/css/*.css")):
        rel = str(path.relative_to(ROOT))
        if rel in EXEMPT:
            continue
        body = strip_comments(path.read_text())
        for label, pat in (("hex colour", HEX), ("colour function", FUNCCOL),
                           ("px font-size", FONTPX), ("literal duration", DURATION)):
            hits = pat.findall(body)
            rep.add("raw-values", f"{rel} declares no {label}", not hits,
                    "" if not hits else f"{len(hits)} found, e.g. {hits[0]!r}")

    for path in sorted(q for q in ROOT.glob("*.html") if not q.name.startswith("_")):
        rel = str(path.relative_to(ROOT))
        inline = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", path.read_text(), re.S))
        inline += "\n".join(re.findall(r'style\s*=\s*"([^"]*)"', path.read_text()))
        body = strip_comments(inline)
        hits = HEX.findall(body) + FUNCCOL.findall(body)
        rep.add("raw-values", f"{rel} declares no inline colour", not hits,
                "" if not hits else f"e.g. {hits[0]!r}")


def check_vars_resolve(rep, defined):
    if not defined:
        return
    used = {}
    for path in list(ROOT.glob("assets/css/*.css")) + list(ROOT.glob("*.html")) + list(ROOT.glob("assets/js/*.js")):
        rel = str(path.relative_to(ROOT))
        if rel in EXEMPT:
            continue
        for v in VARUSE.findall(path.read_text()):
            used.setdefault(v, set()).add(rel)
    unknown = {v: f for v, f in used.items() if v not in defined}
    rep.add("tokens", "every var() resolves to a defined token", not unknown,
            "" if not unknown else "; ".join(f"{v} in {sorted(f)[0]}" for v, f in list(unknown.items())[:4]))
    if used:
        rep.add("tokens", "the system is actually used", True, f"{len(used)} distinct tokens referenced")


def check_markup(rep):
    for path in sorted(q for q in ROOT.glob("*.html") if not q.name.startswith("_")):
        rel = str(path.relative_to(ROOT))
        html = path.read_text()

        h1 = len(re.findall(r"<h1\b", html, re.I))
        rep.add("markup", f"{rel} has exactly one <h1>", h1 == 1, f"found {h1}")

        levels = [int(m) for m in re.findall(r"<h([1-6])\b", html, re.I)]
        jumps = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
        rep.add("markup", f"{rel} heading levels do not skip", not jumps,
                "" if not jumps else f"h{jumps[0][0]} -> h{jumps[0][1]}")

        imgs = re.findall(r"<img\b[^>]*>", html, re.I)
        bad = [t for t in imgs if not (re.search(r'\balt\s*=', t, re.I)
                                       and re.search(r'\bwidth\s*=', t, re.I)
                                       and re.search(r'\bheight\s*=', t, re.I)
                                       and re.search(r'loading\s*=\s*"lazy"', t, re.I))]
        rep.add("markup", f"{rel} images carry alt/width/height/lazy", not bad,
                "" if not bad else f"{len(bad)} of {len(imgs)} incomplete")

        ext = [u for u in re.findall(r'(?:src|href)\s*=\s*"(https?://[^"]+)"', html)
               if not re.match(r"https://fonts\.(googleapis|gstatic)\.com(/|$)", u)]
        rep.add("markup", f"{rel} loads nothing off-host but Google Fonts", not ext,
                "" if not ext else ext[0][:60])

        rep.add("markup", f"{rel} declares lang", bool(re.search(r'<html[^>]*\blang=', html, re.I)))


def check_a11y_css(rep):
    css = "\n".join(p.read_text() for p in ROOT.glob("assets/css/*.css"))
    rep.add("a11y", "a visible focus state is defined", ":focus-visible" in css)
    rep.add("a11y", "reduced motion is honoured",
            "prefers-reduced-motion" in css or
            any("prefers-reduced-motion" in p.read_text() for p in ROOT.glob("assets/js/*.js")))
    rep.add("a11y", "wide content gets its own scroll container",
            bool(re.search(r"overflow-x\s*:\s*auto", css)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    rep = Report()
    defined = check_tokens_exist(rep)
    check_no_raw_values(rep)
    check_vars_resolve(rep, defined)
    check_markup(rep)
    check_a11y_css(rep)

    if args.as_json:
        print(json.dumps({"verdict": "PASS" if rep.passed else "FAIL",
                          "checks": rep.checks, "failures": len(rep.failures)},
                         indent=2, ensure_ascii=False))
    else:
        cur = None
        for c in rep.checks:
            if c["gate"] != cur:
                cur = c["gate"]; print(f"\n{cur}")
            mark = "OK  " if c["passed"] else "FAIL"
            det = f"  ({c['detail']})" if c["detail"] else ""
            print(f"  {mark}  {c['check']}{det}")
        print()
        print(f"PASS — {len(rep.checks)} checks" if rep.passed
              else f"FAIL — {len(rep.failures)} of {len(rep.checks)} checks failed")
    return 0 if rep.passed else 1


if __name__ == "__main__":
    sys.exit(main())
