#!/usr/bin/env python3
"""Deterministic gate for research entries.

CONTENT.md is the contract. This enforces it, so that an entry which claims a
measurement really carries a source, and one that carries no source says so.

    python3 scripts/validators/validate_content.py
"""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "content/index.json"

EVIDENCE = {"SOURCE_FACT", "CALCULATED", "INFERRED", "ILLUSTRATIVE"}
EVIDENCE_NEEDS = {
    "SOURCE_FACT": ("source",),
    "CALCULATED": ("inputs", "yields"),
    "INFERRED": ("reasoning",),
    "ILLUSTRATIVE": (),
}

TOP_REQUIRED = ("id", "number", "title", "year", "tags", "meta", "summary", "blocks")

BLOCK_REQUIRED = {
    "prose":    ("text",),
    "figure":   ("src", "alt", "width", "height", "caption", "evidence"),
    "data":     ("caption", "evidence", "columns", "rows"),
    "equation": ("expr", "evidence"),
    "spec":     ("items",),
    "code":     ("lang", "text"),
    "note":     ("kind", "text"),
    "refs":     ("items",),
}
NEEDS_EVIDENCE = {"figure", "data", "equation"}


class Report:
    def __init__(self): self.checks = []
    def add(self, gate, name, ok, detail=""):
        self.checks.append({"gate": gate, "check": name, "passed": bool(ok), "detail": detail})
    @property
    def failures(self): return [c for c in self.checks if not c["passed"]]
    @property
    def passed(self): return not self.failures


def check_evidence(rep, where, obj):
    cls = obj.get("evidence")
    if cls not in EVIDENCE:
        rep.add("evidence", f"{where} has a valid evidence class", False,
                f"got {cls!r}, expected one of {sorted(EVIDENCE)}")
        return
    missing = [f for f in EVIDENCE_NEEDS[cls] if not obj.get(f)]
    rep.add("evidence", f"{where} ({cls}) carries its provenance", not missing,
            "" if not missing else f"missing {', '.join(missing)}")


def check_entry(rep, path: Path):
    rel = str(path.relative_to(ROOT))
    if not path.is_file():
        rep.add("entries", rel, False, "missing"); return
    try:
        e = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        rep.add("entries", f"{rel} parses", False, str(exc)); return
    rep.add("entries", f"{rel} parses", True, f"{path.stat().st_size} bytes")

    for k in TOP_REQUIRED:
        if k not in e:
            rep.add("entries", f"{rel} has '{k}'", False, "missing")

    blocks = e.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        rep.add("entries", f"{rel} has blocks", False, "empty or not a list"); return

    for i, b in enumerate(blocks):
        where = f"{rel} block[{i}]"
        t = b.get("type")
        if t not in BLOCK_REQUIRED:
            rep.add("blocks", f"{where} has a known type", False,
                    f"got {t!r}, expected one of {sorted(BLOCK_REQUIRED)}")
            continue
        missing = [f for f in BLOCK_REQUIRED[t] if b.get(f) in (None, "", [], {})]
        rep.add("blocks", f"{where} ({t}) is complete", not missing,
                "" if not missing else f"missing {', '.join(missing)}")

        if t in NEEDS_EVIDENCE and not missing:
            check_evidence(rep, where, b)

        if t == "figure":
            for dim in ("width", "height"):
                v = b.get(dim)
                rep.add("blocks", f"{where} {dim} is a number", isinstance(v, int) and v > 0,
                        "" if isinstance(v, int) and v > 0 else f"got {v!r} — the page will reflow without it")

        if t == "data" and isinstance(b.get("rows"), list) and isinstance(b.get("columns"), list):
            ncol = len(b["columns"])
            bad = [r for r in b["rows"] if not isinstance(r, list) or len(r) != ncol]
            rep.add("blocks", f"{where} rows match the column count", not bad,
                    "" if not bad else f"{len(bad)} row(s) not {ncol} wide")

        if t == "spec" and isinstance(b.get("items"), list):
            for j, it in enumerate(b["items"]):
                if not all(it.get(k) for k in ("k", "v")):
                    rep.add("blocks", f"{where} item[{j}] has k and v", False, "incomplete")
                elif "evidence" in it:
                    check_evidence(rep, f"{where} item[{j}]", it)

        if t == "refs" and isinstance(b.get("items"), list):
            for j, it in enumerate(b["items"]):
                resolves = any(it.get(k) for k in ("doi", "arxiv", "url", "file"))
                rep.add("citations", f"{where} ref[{j}] resolves to something", resolves,
                        "" if resolves else "no doi, arxiv, url or file — a citation must reach something real")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    rep = Report()

    if not INDEX.is_file():
        rep.add("index", "content/index.json exists", False, "missing")
    else:
        try:
            idx = json.loads(INDEX.read_text())
            entries = idx.get("entries", [])
            rep.add("index", "content/index.json lists entries", bool(entries), f"{len(entries)} listed")
            for row in entries:
                f = row.get("file")
                if not f:
                    rep.add("index", f"entry {row.get('id')!r} names a file", False, "missing 'file'")
                    continue
                check_entry(rep, ROOT / f)
        except json.JSONDecodeError as exc:
            rep.add("index", "content/index.json parses", False, str(exc))

    if args.as_json:
        print(json.dumps({"verdict": "PASS" if rep.passed else "FAIL",
                          "checks": rep.checks, "failures": len(rep.failures)},
                         indent=2, ensure_ascii=False))
    else:
        cur = None
        for c in rep.checks:
            if c["gate"] != cur:
                cur = c["gate"]; print(f"\n{cur}")
            print(f"  {'OK  ' if c['passed'] else 'FAIL'}  {c['check']}" + (f"  ({c['detail']})" if c["detail"] else ""))
        print()
        print(f"PASS — {len(rep.checks)} checks" if rep.passed
              else f"FAIL — {len(rep.failures)} of {len(rep.checks)} checks failed")
    return 0 if rep.passed else 1


if __name__ == "__main__":
    sys.exit(main())
