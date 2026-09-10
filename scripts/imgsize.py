"""Read an asset's real pixel size, so pages can reserve space for it.

Every image on the site shipped without width/height, which means the browser
cannot reserve a box and the layout jumps as each one arrives. The numbers must
come from the file: a typed dimension that drifts from the asset is worse than
none, because it reserves the wrong box.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=512)
def size(rel: str) -> tuple[int, int] | None:
    """(width, height) for a repo-relative asset path, or None if unreadable."""
    p = ROOT / rel.lstrip("/")
    if not p.exists():
        return None
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.size
    except Exception:
        return None


def attrs(rel: str) -> str:
    """` width="W" height="H"` for an <img>, or "" when there is nothing to state.

    An SVG has no intrinsic pixel size worth declaring — its viewBox already
    fixes the aspect ratio, which is what reserving the box actually needs.
    """
    if rel.lower().endswith(".svg"):
        return ""
    wh = size(rel)
    return f' width="{wh[0]}" height="{wh[1]}"' if wh else ""
