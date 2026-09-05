#!/usr/bin/env python3
"""Prove the copy was actually replaced.

validate_structure.py proves nothing broke. It passes trivially when nothing
happened at all — which is how a worker once reported success on a section it
had not touched. This is the other half: the page must no longer carry the
base's copy, and must carry this project's.

    python3 scripts/validators/validate_copy.py
"""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "index.html"

# Copy that belongs to the design study this was built from. None of it may
# survive; the site is not about that company.
FOREIGN = [
    "WEBISOFT", "WBSFT", "Webisoft", "webisoft",
    "MTL (CAN)", "DEVELOPMENT<br />LABS",
    "A SPECIALIST TEAM", "DIGITAL PRODUCT ENGINEERS",
    "OUR CLIENTS", "Startups", "Enterprises", "Web 3 Companies",
    "FROM IDEA TO IMPACT", "BUILT FOR COMPLEXITY", "NEW POSSIBILITIES",
    "FORWARD THINKING", "DIRECT COLLABORATION", "ENGINEERING DEPTH",
    "ADAPTABILITY", "A SHARED PERSPECTIVE", "Good software starts",
    "BUILT WITH INTENTION", "Advisory", "Blockchain",
    "Product Development", "Enterprise Software", "Artificial Intelligence",
    "Montréal", "Miami",
]

# Copy that must be present, section by section, so a skipped section is loud.
REQUIRED = {
    "identity": ["SHP®", "PARK<br />SEONGHYEON"],
    "hero":     ["RESEARCH IN OPTICALLY", "SEOUL (KR)", "MAGNETOMETRY_"],
    "about":    ["원자의 세차운동"],
    "services": ["광학 설계", "증기셀과 원자물리", "파라메트릭 CAD",
                 "신호와 검증", "감독형 파이프라인",
                 "D1 794.98 nm", "D2 780.24 nm", "Evidence classes"],
    "clients":  ["Rb 증기셀 광학계", "균형 편광계 설계", "감독형 검증 파이프라인"],
    "expertise":["ATOMIC MAGNETOMETRY", "MEASURED, NOT ASSUMED", "EVIDENCE FIRST"],
    "manifesto":["RECORDED TO BE CHECKED"],
    "contact":  ["SHP®"],
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    html = PAGE.read_text()
    checks = []

    for s in FOREIGN:
        n = html.count(s)
        checks.append(("foreign copy", f"{s!r} is gone", n == 0,
                       "" if n == 0 else f"still present {n}x"))

    for section, needles in REQUIRED.items():
        missing = [s for s in needles if s not in html]
        checks.append(("sections", f"{section} carries its copy", not missing,
                       "" if not missing else f"missing {missing[:3]}"))

    failures = [c for c in checks if not c[2]]
    ok = not failures

    if args.as_json:
        print(json.dumps({"verdict": "PASS" if ok else "FAIL",
                          "checks": [{"gate": g, "check": c, "passed": p, "detail": d}
                                     for g, c, p, d in checks],
                          "failures": len(failures)}, indent=2, ensure_ascii=False))
    else:
        cur = None
        for g, c, p, d in checks:
            if not p or g != cur:
                if g != cur:
                    print(f"\n{g}"); cur = g
                if not p:
                    print(f"  FAIL  {c}" + (f"  ({d})" if d else ""))
        print()
        if ok:
            print(f"PASS — {len(checks)} checks, nothing foreign left")
        else:
            print(f"FAIL — {len(failures)} of {len(checks)} checks failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
