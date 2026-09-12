#!/usr/bin/env python3
"""Prove every equation is typeset and every citation resolves.

Three ways this can rot, all of them silent:

  - an equation is edited but render_math.mjs is never re-run, so the page
    keeps showing the previous formula while the JSON says something else;
  - a source id is renamed or removed and the equations pointing at it render
    the bare id instead of a citation;
  - a source that says it is on disk is not, or has been replaced.

    python3 scripts/validators/validate_math.py [--json]
"""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "content" / "entries"
MATH = ROOT / "content" / "math.json"
SOURCES = ROOT / "content" / "sources.json"

CLASSES = {"SOURCE_FACT", "CALCULATED", "INFERRED", "ILLUSTRATIVE"}
HELD = {"disk", "zotero", "named", "standard"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    math = json.loads(MATH.read_text())
    src = {k: v for k, v in json.loads(SOURCES.read_text()).items()
           if not k.startswith("_")}
    checks = []

    def ck(gate, what, ok, detail=""):
        checks.append((gate, what, bool(ok), detail))

    # ── the registry itself ──────────────────────────────────────────────
    for k, v in src.items():
        ck("sources", f"{k}: held is one of {sorted(HELD)}", v.get("held") in HELD,
           "" if v.get("held") in HELD else f"got {v.get('held')!r}")
        ck("sources", f"{k}: has a label", bool(v.get("label")))
        if v.get("held") == "disk":
            p = ROOT / v["path"]
            ck("sources", f"{k}: the file is there", p.exists(),
               "" if p.exists() else f"missing {v['path']}")
            if p.exists() and v.get("sha256"):
                got = hashlib.sha256(p.read_bytes()).hexdigest()
                ck("sources", f"{k}: sha256 still matches", got == v["sha256"],
                   "" if got == v["sha256"] else f"on disk {got[:16]}…")
        # A claim to have read something must come with a way to find it.
        if v.get("held") in ("zotero", "named"):
            ck("sources", f"{k}: cites a doi or url",
               bool(v.get("doi") or v.get("url")))

    # ── every equation ───────────────────────────────────────────────────
    used, n_eq = set(), 0
    for f in sorted(ENTRIES.glob("*.json")):
        e = json.loads(f.read_text())
        no = e["no"]
        for i, q in enumerate(((e.get("geometry") or {}).get("equations") or [])):
            n_eq += 1
            tag = f"{no} eq {i + 1}"
            ck("equations", f"{tag}: has tex", bool(q.get("tex")))
            ck("equations", f"{tag}: is typeset",
               q.get("tex") in math,
               "" if q.get("tex") in math
               else "not in content/math.json — run: node scripts/render_math.mjs")
            ck("equations", f"{tag}: names a source", q.get("src") in src,
               "" if q.get("src") in src else f"unknown source {q.get('src')!r}")
            ck("equations", f"{tag}: carries an evidence class",
               q.get("class") in CLASSES,
               "" if q.get("class") in CLASSES else f"got {q.get('class')!r}")
            # Pointing at a real paper without saying where in it is not a citation.
            if q.get("src") in src and src[q["src"]]["held"] in ("disk", "zotero"):
                ck("equations", f"{tag}: says where in the source", bool(q.get("where")))
            used.add(q.get("src"))

    # An entry claiming SOURCE_FACT from something this repo does not hold has
    # to be caught here, not by a reader.
    for f in sorted(ENTRIES.glob("*.json")):
        e = json.loads(f.read_text())
        for i, q in enumerate(((e.get("geometry") or {}).get("equations") or [])):
            if q.get("src") in src and src[q["src"]]["held"] == "named":
                ck("equations",
                   f"{e['no']} eq {i + 1}: an unheld source cannot be SOURCE_FACT",
                   q.get("class") != "SOURCE_FACT",
                   "" if q.get("class") != "SOURCE_FACT"
                   else f"{q['src']} is not held here")

    for k in sorted(set(src) - used):
        ck("sources", f"{k}: is actually cited", False, "in the registry, used by nothing")

    # ── artifacts point at files that exist ──────────────────────────────
    # Entries list artifact paths relative to the repository named in their
    # `repo` field, which is not always this one. W/03 had no repo field at all,
    # so six paths sat on the page with nothing saying where to find them.
    OTHER = {"opm-freecad-cli": Path("/Users/hyeon/Projects/opm-freecad-cli"),
             "research-agent": Path("/Users/hyeon/orca/projects/research-agent")}
    for f in sorted(ENTRIES.glob("*.json")):
        e = json.loads(f.read_text())
        repo = e.get("repo") or ""
        ck("artifacts", f"{e['no']}: names where its work lives", bool(repo),
           "" if repo else "no repo field, so its artifact paths resolve nowhere")
        root = next((v for k, v in OTHER.items() if repo.startswith(k)), ROOT)
        # Only this repository's own paths can be checked from here; a path in
        # another checkout is verified when that checkout is present.
        if root is ROOT:
            for a in e.get("artifacts", []):
                ck("artifacts", f"{e['no']}: {a['path']}", (root / a["path"]).exists(),
                   "" if (root / a["path"]).exists() else "not in this repository")
        elif root.exists():
            for a in e.get("artifacts", []):
                ck("artifacts", f"{e['no']}: {a['path']} in {repo}",
                   (root / a["path"]).exists(),
                   "" if (root / a["path"]).exists() else f"not in {repo}")

    # ── the cache holds nothing stale ────────────────────────────────────
    tex = {q["tex"] for f in ENTRIES.glob("*.json")
           for q in (((json.loads(f.read_text()).get("geometry") or {}).get("equations")) or [])
           if q.get("tex")}
    extra = set(math) - tex
    ck("cache", "no orphaned entries in math.json", not extra,
       "" if not extra else f"{len(extra)} typeset but unused")

    fails = [c for c in checks if not c[2]]
    ok = not fails
    if args.as_json:
        print(json.dumps({"verdict": "PASS" if ok else "FAIL",
                          "equations": n_eq, "sources": len(src),
                          "checks": [{"gate": g, "check": c, "passed": p, "detail": d}
                                     for g, c, p, d in checks],
                          "failures": len(fails)}, indent=2, ensure_ascii=False))
    else:
        for g, c, p, d in checks:
            if not p:
                print(f"  FAIL  [{g}] {c}" + (f"  ({d})" if d else ""))
        print()
        print(f"PASS — {n_eq} equations typeset, every citation resolves, "
              f"{len(src)} sources" if ok
              else f"FAIL — {len(fails)} of {len(checks)} checks failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
