#!/usr/bin/env python3
"""Render index.html and en/index.html from one template and two string files.

Two hand-maintained translations drift: a section gets added to one and not the
other, a link is fixed in one and not the other, and nobody notices because both
pages still look fine on their own. Generating both from the same code makes
that impossible — the structure is written once, and content/site.{ko,en}.json
supply only the words.

    python3 scripts/build_index.py
    python3 scripts/build_index.py --check     # report drift, write nothing

The work cards are left alone: build_entries.py owns them and splices between
its own markers, so this writes the markers and nothing between them on a first
build, then leaves whatever is there on later ones.
"""
from __future__ import annotations
import argparse, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
MARK_A = "<!-- entries:start -->"
MARK_B = "<!-- entries:end -->"

def esc(x) -> str:
    return html.escape(str(x), quote=True)

def render(s: dict) -> str:
    d = s["dir"]                      # "." for ko at the root, ".." for en/
    o = s["other"]
    p: list[str] = []
    A = p.append

    A(f'''<!doctype html>
<html lang="{esc(s["lang"])}" data-pal="mono">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(s["title"])}</title>
<meta name="description" content="{esc(s["description"])}" />
<meta name="color-scheme" content="light dark" />
<meta property="og:title" content="{esc(s["title"])}" />
<meta property="og:description" content="{esc(s["description"])}" />
<meta property="og:type" content="website" />
<meta property="og:image" content="{esc(s["base_url"])}/assets/gb/hero.png" />
<meta property="og:url" content="{esc(s["canonical"])}" />
<meta property="og:locale" content="{esc(s["lang"])}" />
<link rel="canonical" href="{esc(s["canonical"])}" />
<meta name="twitter:card" content="summary_large_image" />
<link rel="icon" href="{d}/assets/gb/wordmark.png" />
<link rel="alternate" hreflang="{esc(s["lang"])}" href="{esc(s["canonical"])}" />
<link rel="alternate" hreflang="{esc(o["code"].lower())}" href="{esc(o["href"])}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="{d}/styles.css" />
<link rel="stylesheet" href="{d}/entry.css" />
<link rel="stylesheet" href="{d}/decor.css" />
<link rel="stylesheet" href="{d}/crt.css" />
<link rel="stylesheet" href="{d}/frames.css" />
<link rel="stylesheet" href="{d}/gameboy.css" />
<script src="{d}/script.js" defer></script>
<script src="{d}/minigame.js" defer></script>
</head>
<body>
<div class="boot" id="boot" hidden>
  <div class="boot-screen">
    <img class="boot-logo" src="{d}/assets/gb/wordmark.png" alt="" />
    <p class="boot-line" aria-hidden="true"></p>
  </div>
  <div class="boot-wipe" aria-hidden="true"></div>
</div>
<p class="boot-live sr-only" role="status" aria-live="polite"></p>
<div class="panel" aria-hidden="true">
  <div class="panel-mask"></div><div class="panel-vig"></div>
  <div class="panel-glass"></div><div class="panel-curve"></div>
</div>
<div class="scan" aria-hidden="true"></div>
<canvas class="rain" aria-hidden="true"></canvas>
<a class="skip" href="#main">{esc(s["skip"])}</a>

<header class="bar">
  <div class="bar-in">
    <a class="mark" href="#home" aria-label="{esc(s["nav"]["home"])}">
      <span class="mark-px" aria-hidden="true"></span><span class="mark-tx">SHP®</span>
    </a>
    <p class="bar-meta"><span>{esc(s["place"])}</span><b aria-hidden="true"></b><span>{esc(s["year"])}</span></p>
    <nav class="bar-nav" aria-label="{esc(s["nav"]["primary"])}">
      <a href="#services">{esc(s["nav"]["services"])}</a>
      <a href="#clients">{esc(s["nav"]["work"])}</a>
      <a href="#expertise">{esc(s["nav"]["about"])}</a>
      <a class="lang" href="{esc(o["href"])}" hreflang="{esc(o["code"].lower())}" lang="{esc(o["code"].lower())}">{esc(o["code"])}</a>
      <a class="btn" href="#contact">{esc(s["nav"]["contact"])}<i aria-hidden="true">▶</i></a>
    </nav>
    <button class="snd" type="button" aria-pressed="false" title="{esc(s["nav"]["sound"])}">
      <span class="snd-px" aria-hidden="true"></span>
      <span class="sr-only">{esc(s["nav"]["sound"])}</span>
    </button>
    <button class="burger" type="button" aria-expanded="false" aria-controls="menu">
      <span aria-hidden="true"></span><span class="sr-only">{esc(s["nav"]["menu"])}</span>
    </button>
  </div>
  <div class="prog" aria-hidden="true"><i></i></div>
  <div class="menu" id="menu" hidden>
    <a href="#services">{esc(s["nav"]["services"])}</a><a href="#clients">{esc(s["nav"]["work"])}</a>
    <a href="#expertise">{esc(s["nav"]["about"])}</a><a href="#contact">{esc(s["nav"]["contact"])}</a>
    <a href="{esc(o["href"])}" hreflang="{esc(o["code"].lower())}">{esc(o["label"])}</a>
  </div>
</header>

<main id="main">
  <section id="home" class="hero">
    <div class="hero-grid">
      <div class="hero-copy">
        <p class="tag">{s["hero"]["tag"]}</p>
        <h1 class="big">SHP<span>®</span></h1>
        <p class="who">{s["hero"]["who"]}</p>
        <p class="lede">{esc(s["hero"]["lede"])}</p>
        <div class="acts">
          <a class="btn big-btn" href="#contact">{esc(s["hero"]["cta"])}<i aria-hidden="true">▶</i></a>
          <a class="btn ghost" href="{d}/gallery.html">{esc(s["hero"]["log"])}<i aria-hidden="true">▶</i></a>
        </div>
      </div>
      <figure class="screen">
        <img src="{d}/assets/gb/hero.png" alt="{esc(s["hero"]["alt"])}" />
        <figcaption class="strip">
          <span>{esc(s["place"])}</span><span>{esc(s["hero"]["strip_right"])}</span><span class="on">{esc(s["hero"]["live"])}</span>
        </figcaption>
      </figure>
    </div>
    <div class="ticker" aria-hidden="true"><div class="ticker-run"></div></div>
  </section>

  <section id="about" class="slab">
    <p class="kicker">{esc(s["about"]["kicker"])}</p>
    <p class="say">{esc(s["about"]["say"])}</p>
    <dl class="facts">''')
    for k, v in s["about"]["facts"]:
        A(f"      <div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>")
    A("    </dl>\n  </section>\n")

    A(f'  <section id="services" class="slab">\n'
      f'    <p class="kicker">{esc(s["services"]["kicker"])}</p>\n    <ol class="svc">')
    for r in s["services"]["rows"]:
        A(f'''      <li>
        <span class="no">{esc(r["no"])}</span>
        <div class="svc-b"><h3>{esc(r["h"])}</h3>
          <p>{esc(r["p"])}</p>
          <p class="fig">{esc(r["fig"])}</p></div>
        <img src="{d}/{esc(r["img"])}" alt="{esc(r["alt"])}" />
      </li>''')
    A("    </ol>\n  </section>\n")

    A(f'  <section id="clients" class="slab">\n'
      f'    <p class="kicker">{esc(s["work"]["kicker"])}</p>\n'
      f'    <div class="work">\n      {MARK_A}\n      {MARK_B}\n    </div>\n  </section>\n')

    A(f'  <section id="expertise" class="slab">\n'
      f'    <p class="kicker">{esc(s["expertise"]["kicker"])}</p>\n    <div class="cols">')
    for c in s["expertise"]["cols"]:
        items = "".join(f"<li>{esc(i)}</li>" for i in c["items"])
        A(f'      <div><h2>{esc(c["h"])}</h2><ul class="sq">{items}</ul></div>')
    A(f'''    </div>
    <p class="manifesto">{esc(s["expertise"]["manifesto"])}</p>
    <figure class="shield">
      <img src="{d}/assets/gb/shield.png" alt="{esc(s["expertise"]["shield_alt"])}" />
    </figure>
  </section>
''')

    A(f'  <section id="contact" class="slab end">\n'
      f'    <h2 class="sr-only">{esc(s["contact"]["sr"])}</h2>\n'
      f'    <p class="kicker">{esc(s["contact"]["kicker"])}</p>\n'
      f'    <p class="big2">{s["contact"]["big"]}<i aria-hidden="true">▶</i></p>\n'
      f'    <ul class="chan">')
    for r in s["contact"]["rows"]:
        val = (f'<a href="{esc(r["href"])}">{esc(r["v"])}</a>' if r.get("href")
               else f'<b>{r["v"]}</b>')
        A(f'      <li><span>{esc(r["k"])}</span>{val}</li>')
    A("    </ul>\n  </section>\n</main>\n")

    A(f'''<div class="pad" role="group" aria-label="{esc(s["pad"]["label"])}">
  <div class="dpad">
    <button class="d up"    type="button" data-act="up"    aria-label="{esc(s["pad"]["up"])}"></button>
    <button class="d left"  type="button" data-act="left"  aria-label="{esc(s["pad"]["left"])}"></button>
    <span class="d hub" aria-hidden="true"></span>
    <button class="d right" type="button" data-act="right" aria-label="{esc(s["pad"]["right"])}"></button>
    <button class="d down"  type="button" data-act="down"  aria-label="{esc(s["pad"]["down"])}"></button>
  </div>
  <div class="ab">
    <button class="ab-b b" type="button" data-act="b" aria-label="{esc(s["pad"]["b"])}"><span>B</span></button>
    <button class="ab-b a" type="button" data-act="a" aria-label="{esc(s["pad"]["a"])}"><span>A</span></button>
  </div>
  <button class="start" type="button" data-act="start">{esc(s["pad"]["start"])}</button>
</div>

<footer class="foot">
  <p class="brand">{esc(s["footer"]["brand"])}</p>
  <p class="credit">{esc(s["footer"]["credit"])}</p>
  <p class="bits" aria-hidden="true"></p>
</footer>
</body>
</html>
''')
    return "\n".join(p)

def keep_entries(new: str, old_path: Path) -> str:
    """Carry over whatever build_entries.py put between its markers."""
    if not old_path.exists():
        return new
    old = old_path.read_text(encoding="utf-8")
    m = re.search(re.escape(MARK_A) + r"(.*?)" + re.escape(MARK_B), old, re.S)
    if not m or not m.group(1).strip():
        return new
    return re.sub(re.escape(MARK_A) + r".*?" + re.escape(MARK_B),
                  lambda _: MARK_A + m.group(1) + MARK_B, new, flags=re.S)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    targets = [(CONTENT / "site.ko.json", ROOT / "index.html"),
               (CONTENT / "site.en.json", ROOT / "en" / "index.html")]
    shapes = []
    changed = []
    for src, out in targets:
        s = json.loads(src.read_text(encoding="utf-8"))
        shapes.append(shape(s))
        body = keep_entries(render(s), out)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or out.read_text(encoding="utf-8") != body:
            changed.append(str(out.relative_to(ROOT)))
            if not a.check:
                out.write_text(body, encoding="utf-8")
    if shapes[0] != shapes[1]:
        sys.exit("site.ko.json and site.en.json have different shapes — "
                 "one of them is missing a key the other has")
    verb = "would write" if a.check else "wrote"
    print(f"2 locales · shapes match · {verb} {len(changed)}"
          + (f" · {', '.join(changed)}" if changed else ""))
    return 1 if a.check and changed else 0

def shape(o):
    if isinstance(o, dict):
        return {k: shape(v) for k, v in o.items()}
    if isinstance(o, list):
        return [shape(x) for x in o]
    return type(o).__name__

if __name__ == "__main__":
    sys.exit(main())
