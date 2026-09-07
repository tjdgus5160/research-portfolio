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
:root{--bg:#f4f4f2;--ink:#101012;--muted:#6c6c72;--line:#d9d9d4;--card:#fff;--accent:#1b3b6f}
:root:not([data-theme=light]) {}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0d0d0f;--ink:#ececee;--muted:#8e8e96;--line:#26262b;--card:#141417;--accent:#8fb4e8}}
:root[data-theme=dark]{--bg:#0d0d0f;--ink:#ececee;--muted:#8e8e96;--line:#26262b;--card:#141417;--accent:#8fb4e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:400 15px/1.55 "Helvetica Neue",Inter,system-ui,-apple-system,sans-serif;
 -webkit-font-smoothing:antialiased}
header{padding:56px 32px 28px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:clamp(26px,4vw,40px);font-weight:600;letter-spacing:-.02em}
.sub{color:var(--muted);max-width:62ch;margin:0}
.meta{margin-top:18px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
nav{display:flex;flex-wrap:wrap;gap:8px;padding:20px 32px;border-bottom:1px solid var(--line);
 position:sticky;top:0;background:var(--bg);z-index:5}
nav button{font:inherit;font-size:12px;letter-spacing:.06em;text-transform:uppercase;
 padding:7px 14px;border:1px solid var(--line);background:transparent;color:var(--muted);
 border-radius:999px;cursor:pointer}
nav button[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
nav button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
main{padding:28px 32px 80px}
.grid{display:grid;gap:26px;grid-template-columns:repeat(auto-fill,minmax(min(330px,100%),1fr))}
figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:3px;
 overflow:hidden;display:flex;flex-direction:column}
figure img{width:100%;height:auto;display:block;background:var(--line)}
figcaption{padding:14px 15px 16px;display:flex;flex-direction:column;gap:9px}
.name{font-size:13px;font-weight:600;letter-spacing:.01em;word-break:break-all}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;padding:3px 8px;
 border:1px solid var(--line);border-radius:999px;color:var(--muted)}
.tag.live{border-color:var(--accent);color:var(--accent)}
.tag.blocked{border-color:#b0413e;color:#b0413e}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:2px 12px;font-size:12px;
 color:var(--muted);font-variant-numeric:tabular-nums}
dt{letter-spacing:.05em;text-transform:uppercase;font-size:10.5px;padding-top:1px}
dd{margin:0;color:var(--ink);word-break:break-word}
details summary{cursor:pointer;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;
 color:var(--muted);list-style:none}
details summary::-webkit-details-marker{display:none}
details summary::before{content:"+ ";}
details[open] summary::before{content:"\\2212 ";}
details pre{margin:8px 0 0;padding:11px;background:var(--bg);border:1px solid var(--line);
 border-radius:2px;font-size:11px;line-height:1.5;white-space:pre-wrap;word-break:break-word;
 max-height:340px;overflow:auto}
.note{font-size:12.5px;color:var(--muted);border-left:2px solid var(--line);padding-left:10px}
footer{padding:28px 32px 60px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media (max-width:620px){header,nav,main,footer{padding-left:18px;padding-right:18px}}
"""

JS = """
const buttons=[...document.querySelectorAll('nav button')];
const cards=[...document.querySelectorAll('figure')];
function apply(f){
  cards.forEach(c=>{c.hidden = f!=='all' && !c.dataset.group.split(' ').includes(f);});
  buttons.forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.filter===f)));
  try{localStorage.setItem('gallery-filter',f)}catch(e){}
}
buttons.forEach(b=>b.addEventListener('click',()=>apply(b.dataset.filter)));
let start='all';
try{const s=localStorage.getItem('gallery-filter');
    if(s&&buttons.some(b=>b.dataset.filter===s))start=s}catch(e){}
apply(start);
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

    parts = [
        "<title>Generated Image Log</title>",
        f"<style>{CSS}</style>",
        "<header>",
        "<h1>Generated image log</h1>",
        '<p class="sub">Every image produced for this portfolio, newest first — the ones '
        'installed on the site and the ones that were rejected or refused, each with the '
        'model, settings and prompt it came from. Provenance is read back out of the PNGs '
        'themselves, so it survives a ComfyUI restart.</p>',
        f'<p class="meta">{len(rows)} images · {n_live} on the site · rebuilt {esc(stamp)}</p>',
        "</header>",
        "<nav>" + "".join(
            f'<button data-filter="{esc(k)}" aria-pressed="false">{esc(v)}</button>'
            for k, v in filters) + "</nav>",
        '<main><div class="grid">',
    ]

    for r in rows:
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
            f'<img src="assets/gallery/{esc(r["thumb"])}" alt="{esc(r["stem"])}" loading="lazy">',
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
        '<footer>Rebuild with <code>python3 scripts/build_gallery.py</code> after any new '
        'batch. Judgements (installed slot, refusal, notes) live in '
        '<code>assets/gallery/manifest.json</code> and are preserved across rebuilds.</footer>',
        f"<script>{JS}</script>",
    ]
    PAGE.write_text("\n".join(parts) + "\n")
    print(f"gallery.html: {len(rows)} images, {new_thumbs} new thumbnails, "
          f"{len(stale)} stale removed, {n_live} installed")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing")
    sys.exit(build(ap.parse_args().check))
