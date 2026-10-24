"""Second-opinion physics/numerics review of our code with an LLM (Gemini or Grok).

The prompt warns that AI tools make confident mistakes (missing 2*pi, wrong signs,
unconverged results). We use a second model as a *reviewer*, never as the source of
results: every number in the README comes from the scripts in tasks/.

    export GEMINI_API_KEY=...   # or XAI_API_KEY=...
    python tools/ai_review.py --provider gemini              # review src/ and tasks/
    python tools/ai_review.py --provider grok --diff main    # review only changes vs main
    python tools/ai_review.py --dry-run                      # save the prompt, call no API

The challenge prompt and TECHNICAL.md are sent as context, so the reviewer
knows the tasks, conventions and every claim we make.
Output goes to reviews/<provider>-<timestamp>.md; we list what we acted on in the README.
"""
import argparse
import datetime as dt
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
    return client.models.generate_content(model=model, contents=prompt).text


def ask_grok(prompt, model):
    from openai import OpenAI          # xAI's API is OpenAI-compatible
    client = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
    r = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["gemini", "grok"], default="gemini")
    p.add_argument("--model", help="model name (defaults: gemini-3.8-flash / grok-4)")
    p.add_argument("--diff", metavar="BASE", help="review only `git diff BASE`")
    p.add_argument("--dry-run", action="store_true", help="save the prompt to reviews/ and stop")
    a = p.parse_args()
    model = a.model or {"gemini": "gemini-3.8-flash", "grok": "grok-4"}[a.provider]
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


if __name__ == "__main__":
    main()
