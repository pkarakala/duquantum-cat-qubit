"""Second-opinion physics/numerics review of our code with an LLM (Gemini or Grok).

The prompt warns that AI tools make confident mistakes (missing 2*pi, wrong signs,
unconverged results). We use a second model as a *reviewer*, never as the source of
results: every number in the README comes from the scripts in tasks/.

    export GEMINI_API_KEY=...   # or XAI_API_KEY=...
    python tools/ai_review.py --provider gemini              # review src/ and tasks/
    python tools/ai_review.py --provider grok --diff main    # review only changes vs main
    python tools/ai_review.py --dry-run                      # save the prompt, call no API
    python tools/ai_review.py --figures                      # Gemini reads each figure vs its claims

The challenge prompt and TECHNICAL.md are sent as context, so the reviewer
knows the tasks, conventions and every claim we make.
Output goes to reviews/<provider>-<timestamp>.md; we list what we acted on in the README.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
from pathlib import Path

from tools_log import log_tool


def with_retry(call, tries=6, wait=10):
    """Retry on 429/503 'model overloaded' errors, waiting 10, 20, 40 ... s."""
    for k in range(tries):
        try:
            return call()
        except Exception as e:  # google.genai.errors.ServerError / ClientError
            code = getattr(e, "code", None) or getattr(e, "status_code", None)
            daily = "PerDay" in str(e)   # free-tier daily quota: waiting minutes won't help
            if code not in (429, 500, 503) or daily or k == tries - 1:
                if daily:
                    print("  Gemini daily free-tier quota used up; progress so far is saved, "
                          "rerun later (or with another --model) to finish.", flush=True)
                raise
            print(f"  Gemini busy ({code}), retrying in {wait} s ...", flush=True)
            time.sleep(wait)
            wait *= 2

ROOT = Path(__file__).resolve().parent.parent
USAGE = {"in": 0, "out": 0}           # Gemini token counts, for docs/tools-log.md

CHECKLIST = """You are reviewing simulation code for the Alice & Bob cat-qubit challenge
(dynamiqs/JAX, Lindblad master equation, memory a + buffer b,
H = g2 a^2 b^dag + g2 a^dag^2 b - eps_d (b + b^dag), alpha^2 = eps_d / g2,
time in microseconds, rates in rad/us with omega = 2 pi f).
Check specifically, citing file and line:
1. Every frequency converted with exactly one factor of 2*pi.
2. Jump operators carry sqrt(rate); signs and conventions match alpha^2 = +eps_d/g2.
3. Truncation: are top-level populations monitored, and is any reported number unconverged?
4. Analytic predictions used as checks are correct (e.g. 1.0b plateau (1 - e^-8)/2,
   parity decay 2 kappa_a <n>, kappa_2 = 4 g2^2 / kappa_b).
5. Fits: fitted window, model, and whether the stated agreement is justified.
6. Anything a judge could challenge. Be concrete; say 'no issue' if none."""


def briefing():
    """Bring the reviewer up to speed: the challenge prompt and our technical layer."""
    parts = []
    for rel in ["docs/challenge_prompt_v4.md", "TECHNICAL.md"]:
        p = ROOT / rel
        if p.exists():
            parts.append(f"### {rel}\n{p.read_text()}")
    return "\n\n".join(parts)


def gather(diff_base=None):
    if diff_base:
        return subprocess.run(["git", "diff", diff_base, "--", "src", "tasks"],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout
    parts = []
    for p in sorted([*ROOT.glob("src/*.py"), *ROOT.glob("tasks/*.py")]):
        parts.append(f"### {p.relative_to(ROOT)}\n```python\n{p.read_text()}\n```")
    return "\n\n".join(parts)


def ask_gemini(prompt, model):
    from google import genai          # pip install google-genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = with_retry(lambda: client.models.generate_content(model=model, contents=prompt))
    count_tokens(r)
    return r.text


def count_tokens(r):
    u = getattr(r, "usage_metadata", None)
    if u:
        USAGE["in"] += u.prompt_token_count or 0
        USAGE["out"] += (u.candidates_token_count or 0) + (getattr(u, "thoughts_token_count", 0) or 0)


def ask_grok(prompt, model):
    from openai import OpenAI          # xAI's API is OpenAI-compatible
    client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content


FIGURE_PROMPT = """You are checking one figure from a cat-qubit simulation (Alice & Bob challenge,
time in microseconds, rates in rad/us, alpha^2 = eps_d/g2 = 4.41) against the claims we make about it.
Look at the image itself, not only the text. For each claim, say whether the plot as drawn supports it:
read values off the axes (peaks, plateaus, crossing times, slopes) and compare with the stated number.
Then list any problem a judge would notice: missing or wrong axis labels or units, a legend that does
not match the curves, a title that overstates the result, unreadable text, a curve that looks unconverged
or noisy. Say 'none' if there is nothing. Be concrete and short.

Figure file: {name}

Our claims tied to this figure (from TECHNICAL.md, with the numbers our scripts computed):
{claims}

The script's saved results for this task (JSON):
{results}"""

FIGURE_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {"type": "array", "items": {"type": "object", "properties": {
            "claim": {"type": "string", "description": "claim number from the table"},
            "verdict": {"type": "string", "enum": ["supported", "contradicted", "cannot tell from figure"]},
            "evidence": {"type": "string", "description": "what you read off the plot"},
        }, "required": ["claim", "verdict", "evidence"]}},
        "presentation_issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["claims", "presentation_issues"],
}


def claims_table():
    """Rows of the TECHNICAL.md claims table as (number, claim, value, source file)."""
    rows = []
    for line in (ROOT / "TECHNICAL.md").read_text().splitlines():
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) == 6 and cells[0].isdigit():
            src = re.search(r"(task_[\w]+?)\.json", cells[4])
            rows.append((cells[0], cells[1], cells[2], src.group(1) if src else ""))
    return rows


def figure_jobs():
    """Pair every figure with the claims and results file of its task.

    figures/task_1_0b_two_photon_loss.png -> results/task_1_0.json, claims mentioning '1.0b'.
    """
    rows = claims_table()
    for png in sorted((ROOT / "figures").glob("task_*.png")):
        m = re.match(r"task_(\d)_(\d)([a-z]?)_", png.stem + "_")
        if not m:
            continue
        # results/task_1_3a.json exists, results/task_1_0b.json does not (1.0 is one file)
        task = next((t for t in (f"task_{m[1]}_{m[2]}{m[3]}", f"task_{m[1]}_{m[2]}")
                     if (ROOT / "results" / f"{t}.json").exists()), f"task_{m[1]}_{m[2]}")
        label = f"{m[1]}.{m[2]}{m[3]}"
        mine = [r for r in rows if r[3] == task and (not m[3] or label in r[1])]
        res = ROOT / "results" / f"{task}.json"
        yield png, mine, res.read_text() if res.exists() else "{}"


def check_figures(model, dry_run=False):
    from google import genai
    from google.genai import types
    jobs = list(figure_jobs())
    client = None if dry_run else genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    out, raw = [], {}
    partial = ROOT / "reviews" / f"figures-partial-{model}.json"   # resume point between runs
    done = json.loads(partial.read_text()) if partial.exists() else {}
    for png, claims, results in jobs:
        text = FIGURE_PROMPT.format(
            name=png.name, results=results,
            claims="\n".join(f"{n}. {c}: {v}" for n, c, v, _ in claims) or "(none: check presentation only)")
        if dry_run:
            print(f"{png.name}: claims {[r[0] for r in claims]}, prompt {len(text):,} chars")
            continue
        if png.name in done:
            v = done[png.name]
            print(f"{png.name}: already checked, reusing", flush=True)
        else:
            print(f"checking {png.name} ...", flush=True)
            v = None
        if v is None:
          r = with_retry(lambda: client.models.generate_content(
            model=model,
            contents=[types.Part.from_bytes(data=png.read_bytes(), mime_type="image/png"), text],
            config=types.GenerateContentConfig(response_mime_type="application/json",
                                               response_json_schema=FIGURE_SCHEMA)))
          count_tokens(r)
          v = json.loads(r.text)
          done[png.name] = v
          partial.write_text(json.dumps(done, indent=2))
        raw[png.name] = v
        for c in v["claims"]:
            out.append(f"| `{png.name}` | {c['claim']} | {c['verdict']} | {c['evidence']} |")
        for issue in v["presentation_issues"]:
            if issue.strip().lower() != "none":
                out.append(f"| `{png.name}` | presentation | issue | {issue} |")
    if dry_run:
        return
    stamp = f"{dt.datetime.now():%Y%m%d-%H%M}"
    (ROOT / "reviews" / f"figures-{stamp}.json").write_text(json.dumps(raw, indent=2))
    md = ROOT / "reviews" / f"figures-{stamp}.md"
    md.write_text(f"# Gemini figure check ({model})\n\n"
                  "Each figure was sent as an image with the claims it supports; "
                  "verdicts are Gemini's reading of the plot, triaged by us in TECHNICAL.md section 5.\n\n"
                  "| Figure | Claim | Verdict | Evidence |\n|---|---|---|---|\n" + "\n".join(out) + "\n")
    print("saved", md)
    partial.unlink(missing_ok=True)
    bad = sum(1 for v in raw.values() for c in v["claims"] if c["verdict"] == "contradicted")
    issues = sum(1 for v in raw.values() for i in v["presentation_issues"] if i.strip().lower() != "none")
    log_tool(f"Gemini API (`{model}`, multimodal)",
             f"Checked {len(raw)} figures as images against their TECHNICAL.md claims (`ai_review.py --figures`)",
             f"{len(raw)} requests, {USAGE['in']:,} in / {USAGE['out']:,} out tokens",
             f"`reviews/{md.name}`", f"{bad} claims contradicted, {issues} presentation issues; triage pending")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["gemini", "grok"], default="gemini")
    p.add_argument("--model", help="model name (defaults: gemini-3.8-flash / grok-4)")
    p.add_argument("--diff", metavar="BASE", help="review only `git diff BASE`")
    p.add_argument("--dry-run", action="store_true", help="save the prompt to reviews/ and stop")
    p.add_argument("--figures", action="store_true", help="multimodal: check each figure against its claims (Gemini)")
    a = p.parse_args()
    model = a.model or {"gemini": "gemini-3.8-flash", "grok": "grok-4"}[a.provider]
    if a.figures:
        (ROOT / "reviews").mkdir(exist_ok=True)
        if not a.dry_run and not os.environ.get("GEMINI_API_KEY"):
            raise SystemExit("set GEMINI_API_KEY in your shell first (never commit it)")
        return check_figures(model, a.dry_run)
    prompt = (CHECKLIST
              + "\n\n## Context: the challenge prompt and our claims\n\n" + briefing()
              + "\n\n## Code to review\n\n" + gather(a.diff))
    (ROOT / "reviews").mkdir(exist_ok=True)
    if a.dry_run:
        out = ROOT / "reviews" / "prompt.tmp"
        out.write_text(prompt)
        print(f"saved {out} ({len(prompt):,} chars, ~{len(prompt) // 4:,} tokens)")
        return
    key = {"gemini": "GEMINI_API_KEY", "grok": "XAI_API_KEY"}[a.provider]
    if not os.environ.get(key):
        raise SystemExit(f"set {key} in your shell first (never commit it)")
    print(f"sending ~{len(prompt) // 4:,} tokens to {model}; this usually takes 30 s to 2 min...", flush=True)
    text = (ask_gemini if a.provider == "gemini" else ask_grok)(prompt, model)
    out = ROOT / "reviews" / f"{a.provider}-{dt.datetime.now():%Y%m%d-%H%M}.md"
    out.write_text(f"# {a.provider} review ({model})\n\n{text}\n")
    print("saved", out)
    tokens = f", {USAGE['in']:,} in / {USAGE['out']:,} out tokens" if USAGE["in"] else ""
    log_tool(f"{'Gemini API' if a.provider == 'gemini' else 'Grok (xAI API)'} (`{model}`)",
             "Physics/numerics code review" + (f" of `git diff {a.diff}`" if a.diff else " of `src/` and `tasks/`"),
             f"1 request{tokens}", f"`reviews/{out.name}`", "triage pending")


if __name__ == "__main__":
    main()
