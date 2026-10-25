"""Render main's write-ups, notebooks, figures and results into site/public/research/.

Usage: python site/scripts/build_research.py <checkout of main>
Needs: pip install markdown nbconvert. Physics content is copied, never edited.
"""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

REPO_URL = "https://github.com/pkarakala/duquantum-cat-qubit/blob/main"
SRC = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parents[1] / "public" / "research"

DOCS = [
    ("task_1", "Task 1: stabilize, converge, prepare", "docs/task_1.md"),
    ("task_2", "Task 2: bit flips, phase flips, readout", "docs/task_2.md"),
    ("methodology", "Methodology and checks", "docs/TECHNICAL.md"),
]

KATEX = """<link rel="stylesheet" href="katex/katex.min.css">
<script defer src="katex/katex.min.js"></script>
<script defer src="katex/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false})"></script>"""

STYLE = """<style>
:root{--bg:#f4f6fb;--fg:#0f172a;--muted:#475569;--line:#d8deea;--accent:#0f766e;--surface:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#0b1020;--fg:#e7ecf6;--muted:#a6b2c8;--line:#2a3654;--accent:#2dd4bf;--surface:#131a2d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--accent)} img{max-width:100%;height:auto;background:#fff;border-radius:8px}
table{border-collapse:collapse;display:block;overflow-x:auto;margin:16px 0}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left}
pre,code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9em}
pre{background:var(--surface);border:1px solid var(--line);padding:12px;overflow-x:auto;border-radius:8px}
.crumb{font-size:.875rem;color:var(--muted)} .math-display{overflow-x:auto}
</style>"""


def shell(title: str, body: str, up: str = "") -> str:
    katex = KATEX.replace("katex/", f"{up}katex/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} · Cat Qubit Academy</title>
{STYLE}{katex}</head><body><main><p class="crumb"><a href="../#/research">← Research</a> · <a href="../#/">Home</a></p>
{body}</main></body></html>"""


def rewrite_link(target: str, figures: set) -> str:
    if not target.startswith("../"):
        return target
    rel = target[3:]
    if rel.startswith("figures/") and rel.endswith((".png", ".gif", ".jpg")):
        figures.add(rel)
        return rel
    if rel.startswith("notebooks/") and rel.endswith(".ipynb"):
        return rel.replace(".ipynb", ".html")
    if rel.startswith("results/") and rel.endswith(".json") and "/" not in rel[len("results/"):]:
        return rel
    if rel.startswith("docs/") or rel.endswith(".md"):
        name = Path(rel).stem
        return f"{'methodology' if name == 'TECHNICAL' else name}.html"
    return f"{REPO_URL}/{rel}"


def github_slug(value: str, separator: str = "-") -> str:
    """Match GitHub's heading anchors so main's in-page links keep working."""
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", separator)


def render_md(text: str, figures: set) -> str:
    # Shield math from the markdown parser, then restore it for KaTeX.
    stash: list[str] = []

    def keep(s: str) -> str:
        stash.append(s)
        return f"@@MATH{len(stash) - 1}@@"

    text = re.sub(r"```math\n(.*?)```", lambda m: keep(f'<div class="math-display">$${html.escape(m[1])}$$</div>'), text, flags=re.S)
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(f"$${html.escape(m[1])}$$"), text, flags=re.S)
    text = re.sub(r"(?<![\\$])\$([^$\n]+?)\$", lambda m: keep(f"${html.escape(m[1])}$"), text)
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"slugify": github_slug}})
    out = re.sub(r'(src|href)="([^"]+)"', lambda m: f'{m[1]}="{rewrite_link(m[2], figures)}"', out)
    for i, s in enumerate(stash):
        out = out.replace(f"@@MATH{i}@@", s)
    return out


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "notebooks").mkdir(parents=True)
    shutil.copytree(Path(__file__).resolve().parent / "vendor" / "katex", OUT / "katex")
    figures: set = set()
    for slug, title, path in DOCS:
        body = render_md((SRC / path).read_text(), figures)
        (OUT / f"{slug}.html").write_text(shell(title, body))
    for rel in sorted(figures):
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if (SRC / rel).exists():
            shutil.copy2(SRC / rel, dest)
    (OUT / "results").mkdir()
    results = sorted((SRC / "results").glob("*.json"))
    for f in results:
        shutil.copy2(f, OUT / "results" / f.name)
    notebooks = sorted((SRC / "notebooks").glob("[0-9]*.ipynb"))
    subprocess.run(
        ["jupyter", "nbconvert", "--to", "html", "--output-dir", str(OUT / "notebooks"), *map(str, notebooks)],
        check=True,
        capture_output=True,
    )
    manifest = {
        "docs": [{"slug": s, "title": t} for s, t, _ in DOCS],
        "notebooks": [n.stem for n in notebooks],
        "results": [f.name for f in results],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {OUT}: {len(DOCS)} docs, {len(figures)} figures, {len(notebooks)} notebooks, {len(results)} results")


if __name__ == "__main__":
    main()
