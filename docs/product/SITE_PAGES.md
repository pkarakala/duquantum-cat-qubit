# Site pages: home (the talk) and research

## Home `#/` = the presentation
`site/src/academy/home.ts`. One section per slide of the submitted walkthrough (`slides/cat-qubit-walkthrough.pdf`, script `walkthrough-script.md`): cover, Task 1, 2.1, 2.2, 2.3, 2.4a–d, then Academy (L4/L8 buttons), sponsors, why.
- Figures: `site/public/talk/*.jpg` (extracted from the deck PDF; `s24a_equations.png` is the Hamiltonian panel cropped from slide 5).
- Text and numbers: the `SLIDES` array. Keep them identical to the deck and script.
- ←/→ and PageUp/PageDown step sections; right-edge dots jump. In-page `#talk-*` links are intercepted so the hash router is not touched.
- Sponsors: `SPONSORS` array. Solana stays "demo only".

## Research
- `#/research` (`site/src/academy/research.ts`): tasks 1.0–2.4 → write-up section, notebook, results JSON.
- `#/inflate`, `#/errors`, `#/readout`, `#/verify` (`site/src/academy/labPages.ts`): main's figures and numbers per topic. Every number must exist in main's docs.
- Static files in `site/public/research/`, generated from a checkout of `main`:

```bash
pip install markdown nbconvert
git worktree add /tmp/main origin/main
python site/scripts/build_research.py /tmp/main   # rewrites site/public/research/
```

It renders `docs/task_1.md`, `docs/task_2.md`, `docs/TECHNICAL.md` (KaTeX vendored in `site/scripts/vendor/katex`, works offline), notebooks 01–09 (nbconvert; their MathJax loads from a CDN), referenced figures and `results/*.json`. Re-run whenever main's docs or notebooks change; if main renames a doc, update `DOCS` in the script and the anchors in `research.ts`.

## Leaderboard `#/challenge`
`showChallenge` in `site/src/academy/routes.ts`. Live rows from `/api/leaderboard`; if the API is absent, empty or down it shows three rows labelled "Sample entries for illustration, not real submissions or physics results".
