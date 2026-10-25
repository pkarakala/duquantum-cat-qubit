"""Shared helpers for the Section 2 research jobs: parameters, truncation rule, JSON output."""
import json
import math
import os
import platform
import time
from pathlib import Path

TWO_PI = 2 * math.pi
G2 = TWO_PI * 0.763
KAPPA_B = TWO_PI * 2.6
KAPPA_A = TWO_PI * 9.3e-3
KAPPA_2 = 4 * G2**2 / KAPPA_B

OUT = Path("results/s2")


def na0(alpha):
    """Memory truncation for a stabilized cat (no inflation transient): 18, 22, 28, 34 at
    alpha = 1.0, 1.4, 2.1, 2.7 (the Task 2.2 table), rounded up to even."""
    n = math.ceil(8.6 * alpha + 9.5)
    return n + (n % 2)


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["_meta"] = {"host": platform.node(), "cpus": os.cpu_count(),
                     "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(data, indent=1, default=float))
    print("wrote", p)
    return p
