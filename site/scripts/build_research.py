"""Render main's write-ups, notebooks, figures and results into site/public/research/.

Usage:
  python site/scripts/build_research.py              # git fetch origin main, build from origin/main
  python site/scripts/build_research.py --ref <rev>  # build from any commit (fetches origin first)
  python site/scripts/build_research.py <checkout>   # build from a local checkout of main
Needs: pip install markdown nbconvert  (or: uv run --with markdown --with nbconvert python ...)

Physics content is copied, never edited. The build is staged in a temp dir and only
swapped into place when it succeeds, so a failure never leaves the site half-empty.
Docs, figures, notebooks or results that main no longer has are skipped with a warning.
Output is deterministic for a given main commit (UTF-8, LF line endings), so re-running
on the same commit is a no-op.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import markdown

REPO_URL = "https://github.com/pkarakala/duquantum-cat-qubit/blob/main"
SITE = Path(__file__).resolve().parents[1]
OUT = SITE / "public" / "research"
# Top-level paths of main that the build reads; anything else is never exported.
SRC_PATHS = ("docs", "figures", "notebooks", "results")
IMAGE_EXT = (".png", ".gif", ".jpg", ".jpeg", ".svg")

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


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def write_text(path: Path, text: str) -> None:
    # Fixed encoding and LF endings: the same commit renders byte-identically on Mac and Windows.
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(*args: str, cwd: Path = SITE) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def export_ref(ref: str, remote: str, fetch: bool, dest: Path) -> str:
    """Fetch, then export the build inputs of `ref` into `dest`. Returns the commit sha."""
    root = Path(git("rev-parse", "--show-toplevel"))  # pathspecs below are repo-root relative
    if fetch:
        branch = ref[len(remote) + 1:] if ref.startswith(remote + "/") else None
        subprocess.run(["git", "fetch", remote, *([branch] if branch else [])], cwd=root, check=True)
    sha = git("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=root)
    present = set(git("ls-tree", "--name-only", sha, cwd=root).splitlines())
    paths = [p for p in SRC_PATHS if p in present]
    for p in SRC_PATHS:
        if p not in present:
            warn(f"{ref} has no {p}/; skipping it")
    if paths:
        # autocrlf off: export main's bytes exactly as committed.
        tar = subprocess.run(["git", "-c", "core.autocrlf=false", "archive", "--format=tar", sha, *paths],
                             cwd=root, check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            kwargs = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
            tf.extractall(dest, **kwargs)
    return sha


class Renderer:
    def __init__(self, src: Path, built_docs: dict) -> None:
        self.src = src
        self.built_docs = built_docs  # "docs/task_2.md" -> "task_2"
        self.figures: set = set()

    def rewrite_link(self, target: str) -> str:
        """Map a link written relative to main's docs/ onto the published research/ tree."""
        if re.match(r"^([a-z][a-z0-9+.-]*:|#|/)", target, re.I):
            return target  # absolute URL, in-page anchor or site-absolute path
        path, sep, frag = target.partition("#")
        rel = posixpath.normpath(posixpath.join("docs", path)) + ("/" if path.endswith("/") else "")
        if rel.startswith("../") or rel == "..":
            return target
        anchor = sep + frag
        if rel.startswith("figures/") and rel.lower().endswith(IMAGE_EXT):
            if (self.src / rel).is_file():
                self.figures.add(rel)
                return rel + anchor
            warn(f"figure {rel} is linked but missing on main; linking to GitHub")
        elif rel.startswith("notebooks/") and rel.endswith(".ipynb") and (self.src / rel).is_file():
            return rel[: -len(".ipynb")] + ".html" + anchor
        elif re.fullmatch(r"results/[^/]+\.json", rel) and (self.src / rel).is_file():
            return rel + anchor
        elif rel in self.built_docs:
            return f"{self.built_docs[rel]}.html{anchor}"
        return f"{REPO_URL}/{rel}{anchor}"

    def render_md(self, text: str) -> str:
        # Shield math from the markdown parser, then restore it for KaTeX.
        stash: list = []

        def keep(s: str) -> str:
            stash.append(s)
            return f"@@MATH{len(stash) - 1}@@"

        text = re.sub(r"```math\n(.*?)```", lambda m: keep(f'<div class="math-display">$${html.escape(m[1])}$$</div>'), text, flags=re.S)
        text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(f"$${html.escape(m[1])}$$"), text, flags=re.S)
        text = re.sub(r"(?<![\\$])\$([^$\n]+?)\$", lambda m: keep(f"${html.escape(m[1])}$"), text)
        out = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"slugify": github_slug}})
        out = re.sub(r'(src|href)="([^"]+)"', lambda m: f'{m[1]}="{self.rewrite_link(m[2])}"', out)
        for i, s in enumerate(stash):
            out = out.replace(f"@@MATH{i}@@", s)
        return out


def shell(title: str, body: str, up: str = "") -> str:
    katex = KATEX.replace("katex/", f"{up}katex/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} · Cat Qubit Academy</title>
{STYLE}{katex}</head><body><main><p class="crumb"><a href="../#/research">← Research</a> · <a href="../#/">Home</a></p>
{body}</main></body></html>"""


def github_slug(value: str, separator: str = "-") -> str:
    """Match GitHub's heading anchors so main's in-page links keep working."""
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return value.replace(" ", separator)


def site_figure_refs() -> set:
    """Figures the app itself shows (e.g. lab pages) must ship even if no write-up links them."""
    refs: set = set()
    for f in (SITE / "src").rglob("*.ts"):
        refs.update(re.findall(r"""["'`](figures/[\w./-]+?\.(?:png|gif|jpe?g|svg))["'`]""", f.read_text(encoding="utf-8")))
    return refs


def convert_notebooks(notebooks: list, out_dir: Path) -> list:
    """nbconvert to HTML; if the batch fails, retry one at a time and skip the bad ones."""
    def run(nbs: list) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-m", "nbconvert", "--to", "html", "--output-dir", str(out_dir), *map(str, nbs)],
                              capture_output=True, text=True)

    if not notebooks:
        return []
    if run(notebooks).returncode == 0:
        done = notebooks
    else:
        done = []
        for nb in notebooks:
            r = run([nb])
            if r.returncode == 0:
                done.append(nb)
            else:
                warn(f"nbconvert failed for {nb.name}; skipping it\n{r.stderr.strip()[-800:]}")
    for nb in done:  # nbconvert writes platform newlines; normalise for reproducible output
        page = out_dir / f"{nb.stem}.html"
        page.write_bytes(page.read_bytes().replace(b"\r\n", b"\n"))
    return done


def build(src: Path, sha: str, out: Path) -> str:
    (out / "notebooks").mkdir(parents=True)
    (out / "results").mkdir()
    shutil.copytree(Path(__file__).resolve().parent / "vendor" / "katex", out / "katex")

    docs = []
    for slug, title, path in DOCS:
        if (src / path).is_file():
            docs.append((slug, title, path))
        else:
            warn(f"{path} not found on main; skipping page {slug}.html")
    r = Renderer(src, {path: slug for slug, _, path in docs})
    for slug, title, path in docs:
        body = r.render_md((src / path).read_text(encoding="utf-8"))
        write_text(out / f"{slug}.html", shell(title, body))

    for rel in sorted(site_figure_refs()):
        if (src / rel).is_file():
            r.figures.add(rel)
        else:
            warn(f"site/src shows {rel} but main has no such figure")
    for rel in sorted(r.figures):
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, dest)

    results = sorted((src / "results").glob("*.json"))
    for f in results:
        shutil.copy2(f, out / "results" / f.name)
    notebooks = convert_notebooks(sorted((src / "notebooks").glob("[0-9]*.ipynb")), out / "notebooks")
    if not docs:
        # Never replace the published pages with a build that has no write-ups (wrong ref or path).
        sys.exit(f"error: none of {[p for _, _, p in DOCS]} found in {src}; leaving {OUT} untouched")

    manifest = {
        "source": {"repo": REPO_URL.rsplit("/blob/", 1)[0], "commit": sha},
        "docs": [{"slug": s, "title": t} for s, t, _ in docs],
        "notebooks": [n.stem for n in notebooks],
        "results": [f.name for f in results],
    }
    write_text(out / "manifest.json", json.dumps(manifest, indent=1) + "\n")
    return f"{len(docs)} docs, {len(r.figures)} figures, {len(notebooks)} notebooks, {len(results)} results"


def swap_into_place(staged: Path) -> None:
    old = OUT.with_name(OUT.name + ".old")
    if old.exists():
        shutil.rmtree(old)
    if OUT.exists():
        OUT.rename(old)
    try:
        staged.rename(OUT)
    except OSError:
        if old.exists():
            old.rename(OUT)
        raise
    if old.exists():
        shutil.rmtree(old)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkout", nargs="?", help="local checkout of main (default: export --ref from git)")
    ap.add_argument("--ref", default="origin/main", help="commit to build from when no checkout is given")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--no-fetch", action="store_true", help="do not git fetch before exporting --ref")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="research-build-") as tmp:
        tmp = Path(tmp)
        if args.checkout:
            src = Path(args.checkout).resolve()
            try:
                sha = git("rev-parse", "HEAD", cwd=src)
            except (subprocess.CalledProcessError, OSError):
                sha = "unknown"
        else:
            src = tmp / "src"
            src.mkdir()
            sha = export_ref(args.ref, args.remote, not args.no_fetch, src)
        staged = Path(tempfile.mkdtemp(prefix=".research-", dir=OUT.parent))
        try:
            shutil.rmtree(staged)  # build() creates it fresh
            summary = build(src, sha, staged)
            swap_into_place(staged)
        finally:
            if staged.exists():
                shutil.rmtree(staged, ignore_errors=True)
    print(f"wrote {OUT} from {sha[:7]}: {summary}")


if __name__ == "__main__":
    main()
