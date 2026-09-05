#!/usr/bin/env python3
"""Prove the design was not touched.

The brief for this build is: keep the design, replace every word. That is easy
to claim and easy to break by accident, so this compares the page's structural
skeleton — element order, classes, ids and the attributes that carry layout —
against the pristine base commit, and fails on any difference.

Text nodes are ignored on purpose. Changing them is the job.

    python3 scripts/validators/validate_structure.py
    python3 scripts/validators/validate_structure.py --base <git-ref> --file index.html
"""

from __future__ import annotations

import argparse, json, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Attributes that describe structure or styling. `src`/`href` are included so a
# swapped image or a rewired link is reported rather than slipping through as
# "content"; alt/title/aria-label are text and are not.
STRUCTURAL = ("class", "id", "style", "width", "height", "type", "role",
              "src", "href", "hidden", "data-contact", "data-tab", "data-panel")

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "source","track","wbr"}


class Skeleton(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        kept = " ".join(f'{k}={a[k]!r}' for k in STRUCTURAL if k in a)
        self.items.append(f"{'  ' * self.depth}<{tag} {kept}".rstrip())
        if tag not in VOID:
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        self.depth = max(0, self.depth - 1)
        self.items.append(f"{'  ' * self.depth}</{tag}>")


def skeleton(html: str) -> list[str]:
    p = Skeleton()
    p.feed(html)
    return p.items


def at_ref(ref: str, rel: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{rel}"],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=None,
                    help="git ref holding the pristine design (default: the commit that adopted it)")
    ap.add_argument("--file", action="append", default=None,
                    help="file to check (repeatable; default index.html and styles.css)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    base = args.base
    if base is None:
        log = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--format=%H %s", "--all"],
            capture_output=True, text=True).stdout.splitlines()
        for line in log:
            if "Adopt the webisoft-recreation build" in line:
                base = line.split()[0]
                break
    if base is None:
        print("FAIL — cannot find the base commit; pass --base <ref>")
        return 1

    files = args.file or ["index.html", "styles.css", "script.js"]
    checks = []
    for rel in files:
        old = at_ref(base, rel)
        new_path = ROOT / rel
        if old is None:
            checks.append((rel, False, "not present in the base commit")); continue
        if not new_path.is_file():
            checks.append((rel, False, "missing from the working tree")); continue
        new = new_path.read_text()

        if rel.endswith(".html"):
            a, b = skeleton(old), skeleton(new)
            if a == b:
                checks.append((rel, True, f"{len(a)} structural nodes unchanged"))
            else:
                diffs = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
                detail = f"{len(diffs)} node(s) differ; first at {diffs[0][0]}: {diffs[0][1].strip()[:60]!r} -> {diffs[0][2].strip()[:60]!r}" \
                    if diffs else f"node count {len(a)} -> {len(b)}"
                checks.append((rel, False, detail))
        else:
            same = old == new
            checks.append((rel, same, "byte-identical" if same else "MODIFIED — this file carries the design"))

    ok = all(c[1] for c in checks)
    if args.as_json:
        print(json.dumps({"base": base[:12], "verdict": "PASS" if ok else "FAIL",
                          "checks": [{"file": f, "passed": p, "detail": d} for f, p, d in checks]},
                         indent=2, ensure_ascii=False))
    else:
        print(f"\nbase {base[:12]}")
        for f, p, d in checks:
            print(f"  {'OK  ' if p else 'FAIL'}  {f:14s} {d}")
        print()
        print("PASS — the design is untouched" if ok else "FAIL — the design changed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
