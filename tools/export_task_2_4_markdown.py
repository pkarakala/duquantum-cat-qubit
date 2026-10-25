#!/usr/bin/env python3
"""Export the report and appendices as readable GitHub Markdown.

Scientific text, equations and figure paths come from the canonical PDF source.
Only document navigation, heading levels and PDF-only layout commands change.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
APPENDIX_ANCHORS = {
    'A': 'appendix-a-circuit-corrections',
    'B': 'appendix-b-definitions-and-numerical-validation',
    'C': 'appendix-c-additional-controls-and-diagnostic-checks',
}


def format_markdown(text, *, appendix=False, first_figure=1):
    text = re.sub(r'^\\(?:Needspace\{[^\n]*\}|clearpage)\s*$', '', text, flags=re.M)
    figure = first_figure
    lines = []
    for line in text.splitlines():
        image = re.fullmatch(r'!\[(.*)\]\(([^)]+)\)(?:\{[^}]*\})?', line)
        if image:
            caption, target = image.groups()
            lines.extend([f'![{caption}]({target})', '', f'**Figure {figure}.** {caption}'])
            figure += 1
        elif line.startswith('#'):
            lines.append('#' + line)
        else:
            def link(match):
                letter = match.group(1)
                path = '' if appendix else 'task_2_4_appendices.md'
                return f'[Appendix {letter}]({path}#{APPENDIX_ANCHORS[letter]})'
            lines.append(re.sub(r'\bAppendix ([ABC])\b', link, line))
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip() + '\n'


def build():
    source = (DOCS / 'task_2_4_final.md').read_text()
    metadata, body = source.split('\n---\n', 1)
    title = re.search(r'^title: "(.*)"$', metadata, flags=re.M).group(1)
    subtitle = re.search(r'^subtitle: "(.*)"$', metadata, flags=re.M).group(1)
    date = re.search(r'^date: "(.*)"$', metadata, flags=re.M).group(1)
    main, appendices = body.split('\\clearpage', 1)
    disclosure = source.split('## AI-assistance disclosure\n', 1)[1].split('## References\n', 1)[0]
    references = source.split('## References\n', 1)[1]
    main = format_markdown(main)
    main += '\n## AI-assistance disclosure\n\n' + disclosure.strip() + '\n'
    main += '\n## References\n\n' + references.strip() + '\n'
    navigation = (
        '[Part (a)](#task-24a-derive-the-readout-hamiltonian) · '
        '[Part (b)](#task-24b-establish-the-contrast-error-trade-off) · '
        '[Part (c)](#task-24c-propose-and-demonstrate-one-protocol) · '
        '[Part (d)](#task-24d-explain-and-validate-the-improvement) · '
        '[Supporting appendices](task_2_4_appendices.md)'
    )
    main = f'# {title}\n\n{subtitle} · {date}\n\n{navigation}\n\n{main}'
    first_appendix_figure = 1 + len(re.findall(r'^!\[', body.split('\\clearpage', 1)[0], flags=re.M))
    appendices = format_markdown(appendices, appendix=True, first_figure=first_appendix_figure)
    appendices = '# Task 2.4: supporting appendices\n\n[Main report: parts (a)-(d)](task_2_4_report.md)\n\n' + appendices
    paths = [DOCS / 'task_2_4_report.md', DOCS / 'task_2_4_appendices.md']
    for path, content in zip(paths, [main, appendices]):
        assert '\\Needspace' not in content and '\\clearpage' not in content
        assert not re.search(r'\)\{width=', content)
        comment = '<!-- Generated from task_2_4_final.md by tools/export_task_2_4_markdown.py. -->\n\n'
        path.write_text(comment + content)
    return paths


if __name__ == '__main__':
    for path in build():
        print(path.relative_to(ROOT))
