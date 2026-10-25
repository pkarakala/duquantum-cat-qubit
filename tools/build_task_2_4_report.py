#!/usr/bin/env python3
"""Typeset the scientific Markdown report with real LaTeX and render every page.

Requires Pandoc, Tectonic, Matplotlib (fonts), PyMuPDF and Pillow. For example:
  brew install pandoc tectonic
  python -m pip install matplotlib pymupdf pillow
  python tools/build_task_2_4_report.py

The Markdown remains authoritative. Only a temporary Pandoc AST is changed:
the first title is promoted to document metadata and paired vector PDF figures
are preferred over raster previews. No scientific prose or numbers are edited.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]


def run(command, *, text=None, cwd=None):
    result = subprocess.run(command, input=text, text=True, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command[0]}\n"
                           +result.stdout[-7000:]+"\n"+result.stderr[-7000:])
    return result.stdout, result.stderr


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_ast(source, pandoc, *, prefer_vector=True, output_directory=None):
    raw, warnings = run([pandoc, str(source), "--from=markdown+tex_math_dollars+raw_tex"
                        "+pipe_tables+link_attributes+implicit_figures", "--to=json"])
    tree = json.loads(raw)
    blocks = tree["blocks"]
    # Keep compact scientific tables together; longtable may otherwise split
    # a five-row result across pages even when it fits on a fresh page.
    spaced = []
    for block in blocks:
        if block.get("t") == "Table":
            c = block["c"]
            rows = len(c[3][1]) + sum(len(body[2]) + len(body[3]) for body in c[4])
            lines = min(30, max(9, rows * 2 + 3))
            spaced.append({"t": "RawBlock", "c": ["latex", r"\Needspace{" + str(lines) + r"\baselineskip}"]})
        spaced.append(block)
    tree["blocks"] = blocks = spaced
    promoted = bool(blocks and blocks[0].get("t") == "Header" and blocks[0]["c"][0] == 1
                    and "title" not in tree.get("meta", {}))
    if promoted:
        tree.setdefault("meta", {})["title"] = {"t": "MetaInlines", "c": blocks.pop(0)["c"][2]}
    assets = []

    def visit(node):
        if isinstance(node, list):
            return [visit(value) for value in node]
        if not isinstance(node, dict):
            return node
        if node.get("t") == "Header" and promoted:
            node["c"][0] = max(1, node["c"][0]-1)
        if node.get("t") == "Link" and output_directory is not None:
            original = node["c"][2][0]
            parsed = urlparse(original)
            if not parsed.scheme and not parsed.netloc and parsed.path:
                target = (source.parent / unquote(parsed.path)).resolve()
                if not target.is_file():
                    raise FileNotFoundError(f"Local report link does not exist: {target}")
                relative = os.path.relpath(target, output_directory).replace(os.sep, "/")
                node["c"][2][0] = relative + ("#" + parsed.fragment if parsed.fragment else "")
        if node.get("t") == "Image":
            original = node["c"][2][0]
            parsed = urlparse(original)
            if parsed.scheme or parsed.netloc:
                raise ValueError(f"Use a local verified figure for reproducible PDF builds: {original}")
            asset = Path(unquote(parsed.path))
            if not asset.is_absolute():
                asset = source.parent/asset
            asset = asset.resolve()
            if not asset.is_file():
                raise FileNotFoundError(f"Figure does not exist: {asset}")
            chosen = asset
            if prefer_vector and asset.suffix.lower() != ".pdf" and asset.with_suffix(".pdf").is_file():
                candidate = asset.with_suffix(".pdf")
                if candidate.read_bytes().startswith(b"%PDF"):
                    chosen = candidate
            if chosen.suffix.lower() not in (".pdf", ".png", ".jpg", ".jpeg"):
                raise ValueError(f"Provide a PDF/PNG/JPEG export for {chosen.name}")
            node["c"][2][0] = str(chosen)
            attributes = node["c"][0][2]
            if not any(key == "width" for key, _ in attributes):
                attributes.append(["width", "95%"])
            if not any(key == "height" for key, _ in attributes):
                attributes.append(["height", "58%"])
            assets.append({"source": original, "selected_file": str(chosen),
                           "sha256": sha256(chosen), "vector_pdf": chosen.suffix.lower() == ".pdf"})
        return {key: visit(value) for key, value in node.items()}

    return visit(tree), assets, warnings


def latex_header():
    import matplotlib
    fonts = Path(matplotlib.get_data_path())/"fonts/ttf"
    directory = str(fonts).replace("\\", "/")+"/"
    return r"""% Layout and font support only; the source supplies scientific content.
\usepackage{fontspec}
\setmainfont{DejaVuSerif.ttf}[Path={FONTDIR},BoldFont=DejaVuSerif-Bold.ttf,ItalicFont=DejaVuSerif-Italic.ttf,BoldItalicFont=DejaVuSerif-BoldItalic.ttf]
\setsansfont{DejaVuSans.ttf}[Path={FONTDIR},BoldFont=DejaVuSans-Bold.ttf]
\setmonofont{DejaVuSansMono.ttf}[Path={FONTDIR},Scale=0.86]
\usepackage{microtype}
\usepackage{xurl}
\usepackage{booktabs,longtable,array}
\usepackage{etoolbox}
\usepackage{fvextra}
\usepackage{caption}
\usepackage{float}
\floatplacement{figure}{H}
\usepackage{fancyhdr}
\usepackage{needspace}
\setlength{\emergencystretch}{2em}
\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.15}
\AtBeginEnvironment{longtable}{\small}
\RecustomVerbatimEnvironment{verbatim}{Verbatim}{breaklines=true,breakanywhere=true,fontsize=\small}
\captionsetup{font=small,labelfont=bf,skip=7pt}
\setkeys{Gin}{width=\linewidth,height=0.56\textheight,keepaspectratio}
\setlength{\textfloatsep}{14pt plus 3pt minus 2pt}
\setlength{\intextsep}{12pt plus 3pt minus 2pt}
\providecommand{\ket}[1]{\lvert#1\rangle}
\providecommand{\bra}[1]{\langle#1\rvert}
\providecommand{\Tr}{\operatorname{Tr}}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small DuQuantum 2026 / Task 2.4}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\setlength{\headheight}{15pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\thepage}\renewcommand{\headrulewidth}{0pt}}
\widowpenalty=10000
\clubpenalty=10000
\displaywidowpenalty=10000
""".replace("FONTDIR", directory)


def render_and_check(pdf, render_dir, *, dpi=110):
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF QA needs PyMuPDF: python -m pip install pymupdf") from exc
    from PIL import Image, ImageDraw
    render_dir.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(pdf)
    pages, violations, thumbnails = [], [], []
    for index, page in enumerate(document):
        text = page.get_text()
        if "\ufffd" in text:
            violations.append({"page": index+1, "issue": "replacement glyph in extracted text"})
        spans = [span for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", []) for span in line.get("spans", [])]
        for span in spans:
            x0, y0, x1, y1 = span["bbox"]
            if min(x0, y0) < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                violations.append({"page": index+1, "issue": "text outside page",
                                   "text": span["text"], "bbox": list(span["bbox"])})
        filename = render_dir/f"page-{index+1:03d}.png"
        page.get_pixmap(matrix=pymupdf.Matrix(dpi/72, dpi/72), alpha=False).save(filename)
        thumbnail = Image.open(filename).convert("RGB")
        thumbnail.thumbnail((300, 425))
        tile = Image.new("RGB", (320, 455), "#eeeeee")
        tile.paste(thumbnail, ((320-thumbnail.width)//2, 8))
        ImageDraw.Draw(tile).text((10, 436), f"Page {index+1}", fill="black")
        thumbnails.append(tile)
        pages.append({"page": index+1, "width_pt": page.rect.width, "height_pt": page.rect.height,
                      "text_characters": len(text), "images": len(page.get_images()),
                      "render": str(filename), "fonts": [list(font) for font in page.get_fonts()]})
    contacts = []
    for start in range(0, len(thumbnails), 12):
        batch = thumbnails[start:start+12]
        sheet = Image.new("RGB", (1280, 455*((len(batch)+3)//4)), "white")
        for position, tile in enumerate(batch):
            sheet.paste(tile, ((position % 4)*320, (position//4)*455))
        filename = render_dir/f"contact-{start//12+1:02d}.png"
        sheet.save(filename)
        contacts.append(str(filename))
    return {"page_count": len(document), "pages": pages, "violations": violations,
            "contact_sheets": contacts, "dpi": dpi,
            "visual_review": "Required: inspect every rendered page before final delivery"}


def build_report(source, output, workdir, *, pandoc="pandoc", tectonic="tectonic",
                 prefer_vector=True, dpi=110):
    source, output, workdir = Path(source).resolve(), Path(output).resolve(), Path(workdir).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    workdir.mkdir(parents=True, exist_ok=True)
    tree, assets, reader_warnings = prepare_ast(source, pandoc, prefer_vector=prefer_vector,
                                              output_directory=output.parent)
    (workdir/"report.ast.json").write_text(json.dumps(tree, ensure_ascii=False, indent=2)+"\n")
    header = workdir/"layout.tex"
    header.write_text(latex_header())
    tex, writer_warnings = run([pandoc, "--from=json", "--to=latex", "--standalone",
        "--include-in-header", str(header), "--pdf-engine=xelatex", "--no-highlight",
        "--variable", "documentclass=article", "--variable", "fontsize=11pt",
        "--variable", "papersize=a4", "--variable", "geometry:margin=0.76in",
        "--variable", "colorlinks=true", "--variable", "linkcolor=blue",
        "--variable", "urlcolor=blue", "--variable", "linestretch=1.02"],
        text=json.dumps(tree), cwd=source.parent)
    tex_path = workdir/"report.tex"
    tex_path.write_text(tex)
    stdout, stderr = run([tectonic, "--untrusted", "--keep-logs", "--keep-intermediates",
                          "--outdir", str(workdir), str(tex_path)], cwd=workdir)
    (workdir/"compiler.stdout.log").write_text(stdout+"\n"+stderr)
    log_path = workdir/"report.log"
    log = log_path.read_text(errors="replace") if log_path.exists() else ""
    overfull = [float(value) for value in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log)]
    missing = [line for line in log.splitlines() if "Missing character:" in line]
    generated = workdir/"report.pdf"
    if not generated.exists():
        raise RuntimeError("Typesetter did not produce its PDF")
    qa = render_and_check(generated, workdir/"render", dpi=dpi)
    qa.update(source=str(source), source_sha256=sha256(source), assets=assets,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        builder_sha256=sha256(__file__), overfull_hbox_pt=overfull,
        overfull_vbox_messages=[line for line in log.splitlines() if "Overfull \\vbox" in line],
        missing_glyph_messages=missing, reader_warnings=reader_warnings,
        writer_warnings=writer_warnings,
        pandoc_version=run([pandoc, "--version"])[0].splitlines()[0],
        tectonic_version=run([tectonic, "--version"])[0].strip())
    qa["machine_checks_pass"] = (not qa["violations"] and not missing
                                 and max(overfull, default=0.) <= 2.
                                 and not qa["overfull_vbox_messages"])
    (workdir/"qa.json").write_text(json.dumps(qa, indent=2)+"\n")
    if not qa["machine_checks_pass"]:
        raise RuntimeError(f"PDF layout or glyph checks failed; inspect {workdir/'qa.json'}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generated, output)
    qa["output"] = str(output)
    qa["pdf_sha256"] = sha256(output)
    (workdir/"qa.json").write_text(json.dumps(qa, indent=2)+"\n")
    return qa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT/"docs/task_2_4_final.md")
    parser.add_argument("--output", type=Path, default=ROOT/"output/pdf/task_2_4_final_report.pdf")
    parser.add_argument("--workdir", type=Path, default=Path("/tmp/cat-qubit-final"))
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--raster-figures", action="store_true")
    parser.add_argument("--dpi", type=int, default=110)
    parser.add_argument("--pdf-tools-path", type=Path,
                        help="Optional isolated dependency directory containing PyMuPDF")
    args = parser.parse_args()
    if args.pdf_tools_path:
        sys.path.insert(0, str(args.pdf_tools_path.resolve()))
    result = build_report(args.source, args.output, args.workdir, pandoc=args.pandoc,
                          tectonic=args.tectonic, prefer_vector=not args.raster_figures, dpi=args.dpi)
    print(json.dumps({key: result[key] for key in
                      ("output", "page_count", "machine_checks_pass", "contact_sheets")}, indent=2))
