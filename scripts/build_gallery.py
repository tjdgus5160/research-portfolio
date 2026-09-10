#!/usr/bin/env python3
"""Rebuild gallery.html from every image ComfyUI has produced.

Run it again after any new batch; it is idempotent and additive.

Provenance comes out of the PNGs themselves. ComfyUI embeds the API graph in a
`prompt` tEXt chunk, so model, sampler, steps, seed and the prompt text survive
even though /history is wiped on restart — which it was, losing 76 of 79 entries.
A manifest at assets/gallery/manifest.json carries the human judgements (which
slot an image is installed in, why one was rejected) across rebuilds, so those
are written once and never re-derived.

    python3 scripts/build_gallery.py            # rebuild
    python3 scripts/build_gallery.py --check    # report drift, write nothing
"""
from __future__ import annotations
import argparse, html, json, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from imgsize import attrs as img_attrs

ROOT = Path(__file__).resolve().parent.parent
SRC = Path("/Users/hyeon/ComfyUI/output")
OUT = ROOT / "assets" / "gallery"
PAGE = ROOT / "gallery.html"
MANIFEST = OUT / "manifest.json"
THUMB_W = 720
JPEG_Q = 82

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: /Users/hyeon/.venv/bin/python -m pip install pillow")


# ---------------------------------------------------------------- provenance
def read_graph(path: Path) -> dict | None:
    try:
        with Image.open(path) as im:
            raw = im.info.get("prompt")
        return json.loads(raw) if raw else None
    except Exception:
        return None


def describe(graph: dict | None) -> dict:
    """Pull the fields that differ between runs out of an API graph."""
    if not graph:
        return {"model": "unknown", "prompt": "", "settings": {}}
    unets, loras, seed, steps, size = [], [], None, None, None
    sampler = scheduler = cfg = None
    positives = []
    for node in graph.values():
        ct, i = node.get("class_type"), node.get("inputs", {})
        if ct == "UNETLoader":
            unets.append(i.get("unet_name", ""))
        elif ct == "LoraLoaderModelOnly":
            loras.append(f'{i.get("lora_name","")} @ {i.get("strength_model")}')
        elif ct == "KSampler":
            seed, steps = i.get("seed"), i.get("steps")
            cfg, sampler = i.get("cfg"), i.get("sampler_name")
            scheduler = i.get("scheduler")
        elif ct == "RandomNoise":
            seed = i.get("noise_seed")
        elif ct == "Ideogram4Scheduler":
            steps = i.get("steps")
            scheduler = f'Ideogram4 mu={i.get("mu")} std={i.get("std")}'
        elif ct == "KSamplerSelect":
            sampler = i.get("sampler_name")
        elif ct == "DualModelGuider":
            cfg = i.get("cfg")
        elif ct in ("EmptyLatentImage", "EmptySD3LatentImage", "EmptyFlux2LatentImage"):
            size = (i.get("width"), i.get("height"))
        elif ct == "CLIPTextEncode":
            t = i.get("text")
            if isinstance(t, str) and t.strip():
                positives.append(t)

    unets = [u for u in unets if u]
    if any("ideogram" in u for u in unets):
        model = "Ideogram 4"
    elif any("krea2" in u for u in unets):
        model = "krea2 turbo"
    else:
        model = unets[0] if unets else "unknown"

    # The longest encode is the positive; a negative, when present, is shorter.
    prompt = max(positives, key=len) if positives else ""
    negative = ""
    if len(positives) > 1:
        rest = [p for p in positives if p is not prompt]
        negative = max(rest, key=len)

    s = {"seed": seed, "steps": steps, "cfg": cfg, "sampler": sampler,
         "scheduler": scheduler, "size": f"{size[0]}x{size[1]}" if size else None,
         "lora": ", ".join(loras) or None}
    return {"model": model, "prompt": prompt, "negative": negative,
            "settings": {k: v for k, v in s.items() if v not in (None, "")}}


# ------------------------------------------------------------------ manifest
def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"notes": {}}


def installed_map() -> dict[str, str]:
    """Which source image is currently installed in which site slot.

    Compared by bytes, so a slot only claims an image that is genuinely the
    same file — a renamed copy still matches, a re-roll does not.
    """
    import hashlib
    def h(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    live = {}
    for slot in sorted((ROOT / "assets").glob("*.png")):
        live[h(slot)] = slot.name
    out = {}
    for src in sorted(SRC.glob("*.png")):
        d = h(src)
        if d in live:
            out[src.name] = live[d]
    return out


# ---------------------------------------------------------------- thumbnails
def make_thumb(src: Path, dst: Path) -> tuple[int, int]:
    with Image.open(src) as im:
        w, h = im.size
        if w > THUMB_W:
            im = im.convert("RGB").resize((THUMB_W, round(h * THUMB_W / w)),
                                          Image.LANCZOS)
        else:
            im = im.convert("RGB")
        im.save(dst, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
        return im.size


# --------------------------------------------------------------------- page
CSS = """
/* The log is part of the site, not a separate document: it inherits the four
   tones, the pixel type and the frames from the same stylesheets the rest of
   the pages use, and only adds the grid. */
.log-head{padding:clamp(40px,6vw,74px) clamp(14px,3vw,34px) clamp(22px,3vw,32px);
  border-bottom:var(--px) solid var(--t0);max-width:1240px;margin:0 auto}
.log-head h1{margin:0 0 14px;font-family:var(--disp);font-size:clamp(18px,3.4vw,34px);
  font-weight:400;line-height:1.4}
.log-head .sub{margin:0;max-width:62ch;color:var(--t1);font-size:14.5px}
.log-head .meta{margin:20px 0 0;font-family:var(--disp);font-size:9px;
  letter-spacing:.12em;color:var(--t1)}
nav.filters{display:flex;flex-wrap:wrap;gap:8px;padding:16px clamp(14px,3vw,34px);
  border-bottom:var(--px) solid var(--t0);position:sticky;top:0;z-index:40;
  background:var(--t3);max-width:1240px;margin:0 auto}
/* the filters became links when each one got its own paginated run, and the
   rule still only styled buttons, so they rendered as default blue underlines */
nav.filters a,nav.filters span[aria-current]{font:inherit;font-family:var(--disp);
  font-size:9px;letter-spacing:.06em;padding:9px 12px;
  border:var(--px) solid var(--t0);background:var(--t3);color:var(--t0);
  text-decoration:none;display:inline-block}
nav.filters a:hover{background:var(--t0);color:var(--t3)}
nav.filters span[aria-current]{background:var(--t0);color:var(--t3)}
nav.filters a:focus-visible{outline:var(--px) solid var(--t0);outline-offset:var(--px)}
.count{align-self:center;font-family:var(--disp);font-size:9px;color:var(--t1);
  letter-spacing:.1em;margin-left:auto}
main.log{padding:26px clamp(14px,3vw,34px) 70px;max-width:1240px;margin:0 auto}
.grid{display:grid;gap:calc(var(--px)*5);
  grid-template-columns:repeat(auto-fill,minmax(min(320px,100%),1fr))}
.grid figure{margin:0;background:var(--t3);display:flex;flex-direction:column;
  border:var(--px) solid var(--t0)}
/* `hidden` is what the filter sets, and an author `display` on the same element
   overrides it. The previous stylesheet forced display:flex here, so the filter
   changed an attribute and hid nothing at all. */
.grid figure[hidden]{display:none}
.grid figure img{width:100%;height:auto;display:block;background:var(--t2);
  image-rendering:auto}
figcaption{padding:12px 13px 14px;display:flex;flex-direction:column;gap:8px}
.name{font-family:var(--disp);font-size:9.5px;word-break:break-all;line-height:1.7}
.tags{display:flex;flex-wrap:wrap;gap:5px}
.tag{font-family:var(--disp);font-size:8px;letter-spacing:.06em;padding:4px 6px;
  border:var(--px) solid var(--t1);color:var(--t1)}
.tag.live{border-color:var(--t0);background:var(--t0);color:var(--t3)}
.tag.blocked{border-style:dashed}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:12px;
  color:var(--t1);font-variant-numeric:tabular-nums}
dt{font-family:var(--disp);font-size:8px;letter-spacing:.08em;padding-top:2px}
dd{margin:0;color:var(--t0);word-break:break-word}
details summary{cursor:pointer;font-family:var(--disp);font-size:8px;
  letter-spacing:.08em;color:var(--t1);list-style:none}
details summary::-webkit-details-marker{display:none}
details summary::before{content:"+ "}
details[open] summary::before{content:"- "}
details pre{margin:8px 0 0;padding:10px;background:var(--t3);
  border:var(--px) solid var(--t1);font-size:11px;line-height:1.6;
  white-space:pre-wrap;word-break:break-word;max-height:320px;overflow:auto}
.note{font-size:12.5px;color:var(--t1);border-left:calc(var(--px)*2) solid var(--t1);
  padding-left:10px}
.pager{display:flex;flex-wrap:wrap;gap:6px;align-items:center;
  padding:30px clamp(14px,3vw,34px) 0;max-width:1240px;margin:0 auto}
.pager a,.pager span{font-family:var(--disp);font-size:9px;letter-spacing:.06em;
  padding:9px 12px;border:var(--px) solid var(--t0);text-decoration:none;color:var(--t0)}
.pager a:hover{background:var(--t0);color:var(--t3)}
.pager [aria-current]{background:var(--t0);color:var(--t3)}
.pager .gap{border:0;color:var(--t1)}
"""

JS = """
/* The log needs no JavaScript: the filters are links and every page arrives
   already filtered. This only remembers which filter you were last on, so the
   header link back to the log returns you there. */
try{
  const here = location.pathname.split('/').pop() || 'gallery.html';
  localStorage.setItem('gallery-page', here);
}catch(e){}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def build(check_only: bool = False) -> int:
    if not SRC.is_dir():
        sys.exit(f"ComfyUI output not found: {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    notes = manifest.get("notes", {})
    live = installed_map()

    rows, new_thumbs = [], 0
    for src in sorted(SRC.glob("*.png")):
        stem = src.stem
        thumb = OUT / f"{stem}.jpg"
        if not thumb.exists():
            new_thumbs += 1
            if not check_only:
                make_thumb(src, thumb)
        info = describe(read_graph(src))
        with Image.open(src) as im:
            full = f"{im.size[0]}x{im.size[1]}"
        blocked = "blocked" in (notes.get(stem, {}).get("status", ""))
        rows.append({
            "stem": stem, "thumb": thumb.name, "full": full,
            "mtime": src.stat().st_mtime, "bytes": src.stat().st_size,
            "slot": live.get(src.name), "note": notes.get(stem, {}).get("note", ""),
            "status": notes.get(stem, {}).get("status", ""), "blocked": blocked,
            **info,
        })

    stale = [p for p in OUT.glob("*.jpg") if not (SRC / f"{p.stem}.png").exists()]
    if check_only:
        print(f"{len(rows)} images | {new_thumbs} thumbnails to build | "
              f"{len(stale)} stale to drop | {len(live)} installed on the site")
        return 1 if (new_thumbs or stale) else 0
    for p in stale:
        p.unlink()

    rows.sort(key=lambda r: r["mtime"], reverse=True)
    MANIFEST.write_text(json.dumps({"notes": notes}, indent=2, ensure_ascii=False) + "\n")

    models = sorted({r["model"] for r in rows})
    n_live = sum(1 for r in rows if r["slot"])
    n_blocked = sum(1 for r in rows if r["blocked"])
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")

    def group(r):
        g = [re.sub(r"[^a-z0-9]+", "-", r["model"].lower())]
        if r["slot"]:
            g.append("installed")
        if r["blocked"]:
            g.append("blocked")
        return " ".join(g)

    filters = [("all", f"All {len(rows)}")]
    filters += [(re.sub(r"[^a-z0-9]+", "-", m.lower()), m) for m in models]
    filters.append(("installed", f"On the site {n_live}"))
    if n_blocked:
        filters.append(("blocked", f"Blocked {n_blocked}"))

    PER = 12                      # a cold load should fetch a dozen thumbnails, not 126

    # A JS filter over a paginated set only searches the twelve rows in front of
    # you, which is worse than useless — it looks like an answer. Each filter
    # gets its own paginated run instead, so the filters are links, they work
    # without JavaScript, and "no results" cannot mean "not on this page".
    def rows_for(key):
        return rows if key == "all" else [r for r in rows if key in group(r).split()]

    def page_name(key, i):
        stem = "gallery" if key == "all" else f"gallery-{key}"
        return f"{stem}.html" if i == 0 else f"{stem}-{i + 1}.html"

    def pager(key, i, pages):
        if len(pages) < 2:
            return ""
        out = ['<nav class="pager" aria-label="pages">']
        out.append(f'<a href="{page_name(key, i-1)}" rel="prev">PREV</a>' if i
                   else '<span class="gap">PREV</span>')
        for j in range(len(pages)):
            near = abs(j - i) <= 2 or j in (0, len(pages) - 1)
            if not near:
                if abs(j - i) == 3:
                    out.append('<span class="gap">…</span>')
                continue
            out.append(f'<span aria-current="page">{j+1}</span>' if j == i
                       else f'<a href="{page_name(key, j)}">{j+1}</a>')
        out.append(f'<a href="{page_name(key, i+1)}" rel="next">NEXT</a>'
                   if i < len(pages) - 1 else '<span class="gap">NEXT</span>')
        out.append("</nav>")
        return "".join(out)

    def head(key, i, pages):
        # A real document shell: the page had no doctype, no lang, no charset
        # and no viewport, and nothing linking back to the site it belongs to.
        return [
        '<!doctype html>',
        '<html lang="ko" data-pal="mono">',
        '<head>',
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        f'<title>생성 이미지 로그 — {i+1}/{len(pages)} — SHP®</title>',
        '<meta name="description" content="이 포트폴리오를 위해 생성한 모든 이미지와 그 출처." />',
        '<meta name="robots" content="noindex, follow" />',
        '<link rel="icon" href="assets/gb/wordmark.png" />',
        '<link rel="preconnect" href="https://fonts.googleapis.com" />',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />',
        '<link rel="stylesheet" href="styles.css" />',
        '<link rel="stylesheet" href="entry.css" />',
        '<link rel="stylesheet" href="crt.css" />',
        '<link rel="stylesheet" href="frames.css" />',
        f'<style>{CSS}</style>',
        '</head>',
        '<body>',
        '<div class="panel" aria-hidden="true"><div class="panel-mask"></div>'
        '<div class="panel-vig"></div><div class="panel-glass"></div>'
        '<div class="panel-curve"></div></div>',
        '<div class="scan" aria-hidden="true"></div>',
        '<header class="bar"><div class="bar-in">'
        '<a class="mark" href="index.html" aria-label="SHP, 사이트로 돌아가기">'
        '<span class="mark-px" aria-hidden="true"></span>'
        '<span class="mark-tx">SHP®</span></a>'
        '<p class="bar-meta"><span>IMAGE LOG</span><b aria-hidden="true"></b>'
        f'<span>{i+1} / {len(pages)}</span></p>'
        '<nav class="bar-nav" aria-label="주요">'
        '<a href="index.html">← 사이트로</a>'
        '<a class="btn" href="index.html#clients">WORK<i aria-hidden="true">▶</i></a>'
        '</nav></div></header>',
    ]

    parts = []
    written = set()
    for key, label in filters:
        krows = rows_for(key)
        pages = [krows[i:i + PER] for i in range(0, len(krows), PER)] or [[]]
        for i, page_rows in enumerate(pages):
            parts = head(key, i, pages) + [
                '<div class="log-head">',
                '<h1>생성 이미지 로그</h1>',
                '<p class="sub">이 포트폴리오를 위해 만든 모든 이미지입니다 — 사이트에 올라간 것과, '
                '반려되거나 거부된 것까지. 각 장이 어떤 모델·설정·프롬프트에서 나왔는지 함께 싣습니다. '
                '출처는 PNG 자체에서 읽으므로 ComfyUI를 다시 시작해도 남습니다.</p>',
                f'<p class="meta">{len(rows)}장 · 사이트에 {n_live}장 · '
                f'{i+1}/{len(pages)} 페이지 · {esc(stamp)} 갱신</p>',
                '</div>',
                '<nav class="filters" aria-label="filters">' + "".join(
                    (f'<span aria-current="true">{esc(v)}</span>' if k == key
                     else f'<a href="{page_name(k, 0)}">{esc(v)}</a>')
                    for k, v in filters)
                    + f'<span class="count">{len(krows)}장 · {len(pages)}쪽</span></nav>',
                '<main class="log"><div class="grid">',
            ]

            for r in page_rows:
                tags = [f'<span class="tag">{esc(r["model"])}</span>']
                if r["slot"]:
                    tags.append(f'<span class="tag live">{esc(r["slot"])}</span>')
                if r["blocked"]:
                    tags.append('<span class="tag blocked">refused</span>')
                s = r["settings"]
                dl = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in s.items())
                dl += f"<dt>full</dt><dd>{esc(r['full'])} · {r['bytes']//1024} KB</dd>"
                body = [
                    f'<figure data-group="{esc(group(r))}">',
                    f'<img src="assets/gallery/{esc(r["thumb"])}" alt="{esc(r["stem"])}"'
                    f'{img_attrs("assets/gallery/" + r["thumb"])} loading="lazy" decoding="async">',
                    "<figcaption>",
                    f'<div class="name">{esc(r["stem"])}</div>',
                    f'<div class="tags">{"".join(tags)}</div>',
                    f"<dl>{dl}</dl>",
                ]
                if r["note"]:
                    body.append(f'<p class="note">{esc(r["note"])}</p>')
                if r["prompt"]:
                    body.append("<details><summary>prompt</summary>"
                                f"<pre>{esc(r['prompt'])}</pre></details>")
                if r.get("negative"):
                    body.append("<details><summary>negative</summary>"
                                f"<pre>{esc(r['negative'])}</pre></details>")
                body.append("</figcaption></figure>")
                parts.append("".join(body))

            parts += [
                "</div></main>",
                pager(key, i, pages),
                '<footer class="foot"><p class="brand">PARK SEONGHYEON®</p>'
                '<p class="credit">PROVENANCE READ BACK OUT OF THE PNGs THEMSELVES</p>'
                '<p class="credit"><a href="index.html" style="color:inherit">'
                '← 포트폴리오로 돌아가기</a></p></footer>',
                f"<script>{JS}</script>",
                "</body>", "</html>",
            ]
            name = page_name(key, i)
            written.add(name)
            (ROOT / name).write_text("\n".join(parts) + "\n", encoding="utf-8")
    # a shorter run than last time leaves pages no pager links to, and a filter
    # that disappeared leaves a whole orphaned set
    for stale_page in ROOT.glob("gallery*.html"):
        if stale_page.name not in written:
            stale_page.unlink()
    print(f"gallery.html: {len(rows)} images, {new_thumbs} new thumbnails, "
          f"{len(stale)} stale removed, {n_live} installed")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing")
    sys.exit(build(ap.parse_args().check))
