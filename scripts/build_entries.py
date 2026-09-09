#!/usr/bin/env python3
"""Build one page per research entry, plus the stage-select cards on the index.

Each entry is a JSON file in content/entries/ shaped like the pipeline that
produces it — question, evidence, method, numbers, geometry, validation, what is
still unknown. Adding research later means adding a file here and re-running;
nothing about the page has to be written by hand.

    python3 scripts/build_entries.py
    python3 scripts/build_entries.py --check    # report drift, write nothing

Every number carries its evidence class, because a page that prints a measured
value and an assumed one in the same style is exactly what this project exists
to prevent.
"""
from __future__ import annotations
import argparse, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "entries"
OUT = ROOT / "work"
INDEX = ROOT / "index.html"

CLASSES = {
    "SOURCE_FACT":  ("SRC", "출처에 적혀 있는 값"),
    "CALCULATED":   ("CALC", "다른 값에서 유도된 값"),
    "INFERRED":     ("INF", "근거를 밝힌 가정"),
    "ILLUSTRATIVE": ("ILL", "그림을 위한 것, 물리적 주장 없음"),
}

def esc(x) -> str:
    return html.escape(str(x), quote=True)

def badge(cls: str) -> str:
    short, title = CLASSES.get(cls, (cls[:4], cls))
    return (f'<abbr class="cls c-{esc(cls.lower())}" title="{esc(cls)} — {esc(title)}">'
            f'{esc(short)}</abbr>')

def load() -> list[dict]:
    entries = []
    for f in sorted(SRC.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["_file"] = f.name
        entries.append(d)
    entries.sort(key=lambda d: d["no"])
    return entries

# ── one entry page ─────────────────────────────────────────────────────────
def page(e: dict, prev: dict | None, nxt: dict | None) -> str:
    p: list[str] = []
    A = p.append
    A(f'''<!doctype html>
<html lang="ko" data-pal="mono">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(e["no"])} {esc(e["title"])} — SHP®</title>
<meta name="description" content="{esc(e.get("summary",""))}" />
<link rel="icon" href="../assets/gb/wordmark.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="../styles.css" />
<link rel="stylesheet" href="../entry.css" />
</head>
<body class="entry">
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="bar">
  <div class="bar-in">
    <a class="mark" href="../index.html" aria-label="SHP, 처음으로">
      <span class="mark-px" aria-hidden="true"></span><span class="mark-tx">SHP®</span>
    </a>
    <p class="bar-meta"><span>{esc(e["no"])}</span><b aria-hidden="true"></b><span>{esc(e.get("date","—"))}</span></p>
    <nav class="bar-nav" aria-label="주요">
      <a href="../index.html#clients">← STAGE SELECT</a>
    </nav>
  </div>
</header>
<main id="main">
  <section class="e-head">
    <p class="kicker">{esc(e["no"])} — {esc(e.get("subtitle",""))}</p>
    <h1 class="e-title">{esc(e["title"])}</h1>
    <p class="e-sum">{esc(e.get("summary",""))}</p>
    <dl class="e-meta">''')
    if e.get("repo"):
        A(f'<div><dt>REPO</dt><dd>{esc(e["repo"])}</dd></div>')
    A(f'<div><dt>STATUS</dt><dd>{esc(e.get("validation",{}).get("verdict","—"))}</dd></div>')
    A(f'<div><dt>DATE</dt><dd>{esc(e.get("date","—"))}</dd></div>')
    A("</dl></section>")

    def sec(n, name, body):
        A(f'<section class="e-sec"><p class="kicker">{n} — {esc(name)}</p>{body}</section>')

    if e.get("question"):
        sec("01", "무엇을 물었나", f'<p class="e-q">{esc(e["question"])}</p>')

    if e.get("evidence"):
        rows = "".join(
            f'<li>{badge(v["class"])}<div><p class="e-claim">{esc(v["claim"])}</p>'
            f'<p class="e-src">{esc(v.get("source") or v.get("reasoning",""))}</p></div></li>'
            for v in e["evidence"])
        sec("02", "근거", f'<ul class="e-ev">{rows}</ul>')

    if e.get("method"):
        rows = "".join(
            f'<li><span class="no">{esc(m["step"])}</span>'
            f'<div><h3>{esc(m["name"])}</h3><p>{esc(m["detail"])}</p></div></li>'
            for m in e["method"])
        sec("03", "어떻게 했나", f'<ol class="e-me">{rows}</ol>')

    if e.get("numbers"):
        rows = "".join(
            f'<tr><th scope="row">{esc(n["name"])}</th>'
            f'<td class="v">{esc(n["value"])}<i>{esc(n.get("unit",""))}</i></td>'
            f'<td>{badge(n["class"])}</td><td class="n">{esc(n.get("note",""))}</td></tr>'
            for n in e["numbers"])
        sec("04", "수치", '<div class="e-scroll"><table class="e-nums">'
            '<thead><tr><th scope="col">값</th><th scope="col">크기</th>'
            '<th scope="col">등급</th><th scope="col">출처 · 식 · 근거</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

    g = e.get("geometry") or {}
    if g.get("renders") or g.get("parametric"):
        b = ""
        if g.get("renders"):
            b += '<div class="e-views">' + "".join(
                f'<figure><img src="../{esc(r["src"])}" alt="{esc(r["alt"])}" loading="lazy" />'
                f'<figcaption><b>{esc(r["view"])}</b>{esc(r.get("note",""))}</figcaption></figure>'
                for r in g["renders"]) + "</div>"
        if g.get("parametric"):
            b += '<ul class="e-par">' + "".join(f"<li>{esc(x)}</li>" for x in g["parametric"]) + "</ul>"
        if g.get("parametric_note"):
            b += f'<p class="e-note">{esc(g["parametric_note"])}</p>'
        if g.get("tolerance"):
            b += f'<p class="e-note">허용오차 {esc(g["tolerance"])}</p>'
        sec("05", "형상", b)

    v = e.get("validation") or {}
    if v.get("checks"):
        rows = "".join(
            f'<tr><th scope="row">{esc(c["name"])}</th><td class="v">{esc(c["result"])}</td>'
            f'<td class="n">{esc(c.get("how",""))}</td></tr>' for c in v["checks"])
        sec("06", "검증", f'<p class="e-verdict">{esc(v.get("verdict","—"))}</p>'
            '<div class="e-scroll"><table class="e-nums"><thead><tr>'
            '<th scope="col">검사</th><th scope="col">결과</th><th scope="col">방법</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')

    if e.get("defect"):
        d = e["defect"]
        sec("07", "발견된 결함", "".join([
            f'<p class="e-q">{esc(d["what"])}</p>',
            '<dl class="e-meta wide">',
            f'<div><dt>찾은 방법</dt><dd>{esc(d.get("found_by",""))}</dd></div>',
            f'<div><dt>원인</dt><dd>{esc(d.get("cause",""))}</dd></div>',
            f'<div><dt>수정</dt><dd>{esc(d.get("fix",""))}</dd></div>',
            f'<div><dt>재발 방지</dt><dd>{esc(d.get("prevention",""))}</dd></div>',
            "</dl>"]))

    if e.get("unknown"):
        n = "08" if e.get("defect") else "07"
        sec(n, "아직 모르는 것", '<ul class="sq e-unk">' +
            "".join(f"<li>{esc(x)}</li>" for x in e["unknown"]) + "</ul>")

    if e.get("artifacts"):
        n = "09" if e.get("defect") else "08"
        rows = "".join(f'<li><code>{esc(a["path"])}</code><span>{esc(a.get("note",""))}</span></li>'
                       for a in e["artifacts"])
        sec(n, "산출물", f'<ul class="e-art">{rows}</ul>')

    A('<nav class="e-nav" aria-label="다른 항목">')
    A(f'<a href="{esc(prev["slug"])}.html">◀ {esc(prev["no"])} {esc(prev["title"])}</a>'
      if prev else "<span></span>")
    A('<a href="../index.html#clients">STAGE SELECT</a>')
    A(f'<a href="{esc(nxt["slug"])}.html">{esc(nxt["no"])} {esc(nxt["title"])} ▶</a>'
      if nxt else "<span></span>")
    A("</nav></main>")
    A('<footer class="foot"><p class="brand">PARK SEONGHYEON®</p>'
      '<p class="credit">EVERY VALUE CARRIES ITS EVIDENCE CLASS</p></footer>')
    A('<script src="../script.js" defer></script></body></html>')
    return "\n".join(p) + "\n"

# ── the stage-select cards on the index ────────────────────────────────────
def cards(entries: list[dict]) -> str:
    out = []
    for e in entries:
        v = e.get("validation") or {}
        n_num = len(e.get("numbers") or [])
        n_chk = len(v.get("checks") or [])
        filled = min(10, max(1, round((n_num + n_chk) / 2)))
        meter = "█" * filled + "░" * (10 - filled)
        out.append(
            f'      <article><span class="no">{esc(e["no"])}</span>'
            f'<h3>{esc(e["title"])}</h3>'
            f'<p>{esc(e.get("summary",""))}</p>'
            f'<p class="stat"><b>{esc(meter)}</b>'
            f'<span>{n_num} VALUES · {n_chk} CHECKS · {esc(v.get("verdict","—"))}</span></p>'
            f'<a class="btn ghost" href="work/{esc(e["slug"])}.html">'
            f'OPEN<i aria-hidden="true">▶</i></a></article>')
    return "\n".join(out)

MARK_A = "<!-- entries:start -->"
MARK_B = "<!-- entries:end -->"

def splice(entries: list[dict], check: bool) -> bool:
    h = INDEX.read_text(encoding="utf-8")
    block = f"{MARK_A}\n{cards(entries)}\n      {MARK_B}"
    if MARK_A in h and MARK_B in h:
        new = re.sub(re.escape(MARK_A) + r".*?" + re.escape(MARK_B), lambda _: block,
                     h, flags=re.S)
    else:
        # The cards contain <div>s of their own, so a non-greedy match to the
        # first </div> closes on the wrong one and leaves orphaned markup
        # behind — which is exactly what happened the first time. Anchor on the
        # section's close instead, which cannot be nested here.
        m = re.search(r'(<div class="work">).*?(</div>\s*</section>)', h, re.S)
        if not m:
            sys.exit("could not find the work container in index.html")
        new = h[:m.end(1)] + "\n      " + block + "\n    " + h[m.start(2):]
    if new == h:
        return False
    if not check:
        INDEX.write_text(new, encoding="utf-8")
    return True

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    entries = load()
    if not entries:
        sys.exit(f"no entries in {SRC}")
    OUT.mkdir(exist_ok=True)
    changed = []
    for i, e in enumerate(entries):
        body = page(e, entries[i - 1] if i else None,
                    entries[i + 1] if i + 1 < len(entries) else None)
        f = OUT / f"{e['slug']}.html"
        if not f.exists() or f.read_text(encoding="utf-8") != body:
            changed.append(f.name)
            if not a.check:
                f.write_text(body, encoding="utf-8")
    idx = splice(entries, a.check)
    verb = "would change" if a.check else "wrote"
    print(f"{len(entries)} entries · {verb} {len(changed)} page(s)"
          f"{' + index' if idx else ''}"
          + (f" · {', '.join(changed)}" if changed else ""))
    return 1 if a.check and (changed or idx) else 0

if __name__ == "__main__":
    sys.exit(main())
