"""Render each entry named by content/index.json into entry-<id>.html at the repository root and write the index-rows fragment to content/index-rows.html, so that adding research means writing JSON, not HTML. index.html is maintained by hand and is never written."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blocks import render_block, esc

REQUIRED = ("id", "number", "title", "year", "summary", "blocks")

PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — 박성현</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;700;800&family=IBM+Plex+Sans+KR:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/css/tokens.css">
<link rel="stylesheet" href="assets/css/base.css">
<link rel="stylesheet" href="assets/css/components.css">
</head>
<body>
<header class="bar"><div class="wrap"><span class="label">SHP · OPM</span><nav><a class="label" href="index.html">← INDEX</a></nav></div></header>
<main><div class="wrap"><article class="entry">
<aside class="entry__rail"><dl class="meta">{rail}</dl></aside>
<div class="entry__body">{body}</div>
</article></div></main>
<footer><div class="wrap"><p class="label">박성현 · SEOUL, KR</p></div></footer>
<script type="module" src="assets/js/site.js"></script>
</body>
</html>
"""


def pair(key, value):
    return f'<dt class="meta__k">{esc(str(key))}</dt><dd class="meta__v">{esc(str(value))}</dd>'


def rail_html(entry):
    pairs = [pair("번호", entry["number"]), pair("연도", entry["year"])]
    if entry.get("status") is not None:
        pairs.append(pair("상태", entry["status"]))
    if entry.get("tags"):
        pairs.append(pair("태그", " · ".join(entry["tags"])))
    for key, value in (entry.get("meta") or {}).items():
        pairs.append(pair(key, value))
    return "\n".join(pairs)


def body_html(entry):
    parts = [f"<h1>{esc(entry['title'])}</h1>"]
    if entry.get("subtitle"):
        parts.append(f'<p class="hero__meta mono">{esc(entry["subtitle"])}</p>')
    parts.append(f"<p>{esc(entry['summary'])}</p>")
    parts.extend(render_block(block) for block in entry["blocks"])
    return "\n".join(parts)


def row_html(entry):
    tags = " · ".join(entry.get("tags") or [])
    return (
        f'<a class="index__row" href="entry-{entry["id"]}.html">\n'
        f'  <span class="index__num mono">{esc(str(entry["number"]))}</span>\n'
        f'  <span class="index__title">{esc(entry["title"])}</span>\n'
        f'  <span class="index__year mono">{esc(str(entry["year"]))}</span>\n'
        f'  <span class="index__tags mono">{esc(tags)}</span>\n'
        f'  <span class="index__arrow" aria-hidden="true">→</span>\n'
        '</a>'
    )


def load_index():
    path = ROOT / "content" / "index.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        names = data
    elif isinstance(data, dict):
        names = data.get("entries", [])
    else:
        raise ValueError("content/index.json must be a list or an object with an 'entries' list")
    files = []
    for name in names:
        if isinstance(name, dict):
            if "file" not in name:
                raise ValueError(f"entry {name.get('id', '?')}: missing 'file' key")
            source = name["file"]
        else:
            source = name
        target = Path(source)
        if not target.is_absolute():
            target = ROOT / target
        if not target.is_file():
            raise FileNotFoundError(target)
        files.append(target)
    return files


def load_entry(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in REQUIRED:
        if key not in data:
            raise ValueError(f"entry {path.name}: missing required key '{key}'")
    return data


def inject_index_rows(rows_html):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    open_marker = "<!-- BUILD:INDEX_ROWS -->"
    close_marker = "<!-- /BUILD:INDEX_ROWS -->"
    start = text.find(open_marker)
    if start == -1:
        raise ValueError(f"missing marker: {open_marker}")
    end = text.find(close_marker, start + len(open_marker))
    if end == -1:
        raise ValueError(f"missing marker: {close_marker}")
    path.write_text(
        text[: start + len(open_marker)] + "\n" + rows_html + "\n" + text[end:],
        encoding="utf-8",
    )


def main():
    written = []
    rows = []
    for path in load_index():
        entry = load_entry(path)
        page = PAGE.format(title=esc(entry["title"]), rail=rail_html(entry), body=body_html(entry))
        out = ROOT / f'entry-{entry["id"]}.html'
        out.write_text(page, encoding="utf-8")
        written.append(out)
        print(f"wrote {out.relative_to(ROOT)}")
        rows.append(row_html(entry))
    rows_path = ROOT / "content" / "index-rows.html"
    rows_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    written.append(rows_path)
    print(f"wrote {rows_path.relative_to(ROOT)}")
    inject_index_rows("\n".join(rows))
    index_path = ROOT / "index.html"
    written.append(index_path)
    print(f"updated {index_path.relative_to(ROOT)}")
    print(f"{len(written)} files written")


if __name__ == "__main__":
    main()
