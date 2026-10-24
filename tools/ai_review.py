"""Second-opinion physics/numerics review of our code with an LLM (Gemini or Grok).

The prompt warns that AI tools make confident mistakes (missing 2*pi, wrong signs,
unconverged results). We use a second model as a *reviewer*, never as the source of
results: every number in the README comes from the scripts in tasks/.

    export GEMINI_API_KEY=...   # or XAI_API_KEY=...
    python tools/ai_review.py --provider gemini              # review src/ and tasks/
    python tools/ai_review.py --provider grok --diff main    # review only changes vs main

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
    p.add_argument("--model", help="model name (defaults: gemini-2.5-pro / grok-4)")
    p.add_argument("--diff", metavar="BASE", help="review only `git diff BASE`")
    a = p.parse_args()
    model = a.model or {"gemini": "gemini-2.5-pro", "grok": "grok-4"}[a.provider]
    prompt = CHECKLIST + "\n\n" + gather(a.diff)
    text = (ask_gemini if a.provider == "gemini" else ask_grok)(prompt, model)
    out = ROOT / "reviews" / f"{a.provider}-{dt.datetime.now():%Y%m%d-%H%M}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"# {a.provider} review ({model})\n\n{text}\n")
    print("saved", out)


if __name__ == "__main__":
    main()
