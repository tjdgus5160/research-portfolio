"""Render content blocks to HTML.

Each block is a dict from an entry JSON; every value read from the JSON is
escaped through :func:`esc` before it reaches the markup.
"""

from html import escape


def esc(v) -> str:
    """Escape &, <, > and " in str(v)."""
    return escape(str(v), quote=True)


def chip(obj) -> str:
    """Evidence chip, or "" when obj has no evidence."""
    ev = obj.get("evidence")
    if not ev:
        return ""
    slug = str(ev).lower().replace("_", "-")
    return f'<span class="chip chip--{slug}">{esc(ev)}</span>'


def render_prose(b) -> str:
    paras = (p for p in b["text"].split("\n\n") if p.strip())
    return "".join(f"<p>{esc(p)}</p>" for p in paras)


def render_figure(b) -> str:
    c = chip(b)
    cap = f'{esc(b["caption"])} {c}' if c else esc(b["caption"])
    return (
        "<figure>"
        f'<img src="{esc(b["src"])}" alt="{esc(b["alt"])}" '
        f'width="{esc(b["width"])}" height="{esc(b["height"])}" loading="lazy">'
        f"<figcaption>{cap}</figcaption>"
        "</figure>"
    )


def render_data(b) -> str:
    c = chip(b)
    cap = f'{esc(b["caption"])} {c}' if c else esc(b["caption"])
    head = "".join(f"<th>{esc(col)}</th>" for col in b["columns"])
    body = "".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
        for row in b["rows"]
    )
    return (
        f"<figcaption>{cap}</figcaption>"
        f'<div class="scroll"><table><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def render_equation(b) -> str:
    out = [f'<p class="mono">{esc(b["expr"])}</p>']
    if b.get("inputs"):
        pairs = "".join(
            f'<dt class="meta__k">{esc(k)}</dt><dd class="meta__v">{esc(v)}</dd>'
            for k, v in b["inputs"].items()
        )
        out.append(f'<dl class="meta">{pairs}</dl>')
    if b.get("yields") is not None:
        out.append(f'<p class="mono">= {esc(b["yields"])}</p>')
    out.append(chip(b))
    if b.get("note"):
        out.append(f'<p class="hero__note">{esc(b["note"])}</p>')
    return "".join(out)


def render_spec(b) -> str:
    out = ['<dl class="meta">']
    for item in b["items"]:
        out.append(f'<dt class="meta__k">{esc(item["k"])}</dt>')
        bits = [esc(item["v"])]
        if item.get("unit"):
            bits.append(esc(item["unit"]))
        c = chip(item)
        if c:
            bits.append(c)
        out.append(f'<dd class="meta__v">{" ".join(bits)}</dd>')
    out.append("</dl>")
    return "".join(out)


def render_code(b) -> str:
    return f'<div class="scroll"><pre><code>{esc(b["text"])}</code></pre></div>'


def render_note(b) -> str:
    return f'<p class="label">{esc(b["kind"])}</p><p>{esc(b["text"])}</p>'


def render_refs(b) -> str:
    items = []
    for r in b["items"]:
        href = None
        if r.get("doi"):
            href, label = f"https://doi.org/{r['doi']}", r["doi"]
        elif r.get("arxiv"):
            href, label = f"https://arxiv.org/abs/{r['arxiv']}", r["arxiv"]
        elif r.get("url"):
            href, label = r["url"], r["url"]
        if href is None:
            items.append(f"<li>{esc(r['text'])}</li>")
        else:
            items.append(
                f"<li>{esc(r['text'])} "
                f'<a href="{esc(href)}">{esc(label)}</a></li>'
            )
    return f"<ol>{''.join(items)}</ol>"


RENDERERS = {
    "prose": render_prose, "figure": render_figure, "data": render_data,
    "equation": render_equation, "spec": render_spec, "code": render_code,
    "note": render_note, "refs": render_refs,
}


def render_block(b) -> str:
    t = b.get("type")
    fn = RENDERERS.get(t)
    if fn is None:
        raise ValueError(f"unknown block type: {t!r}")
    return f'<section class="block block--{esc(t)} reveal">{fn(b)}</section>'
