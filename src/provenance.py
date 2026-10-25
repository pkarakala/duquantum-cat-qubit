"""Provenance block for every record: git state, package versions and platform.

dirty is True when src/, tasks/ or tools/ have uncommitted changes, so a production record
proves it came from committed code. Never stores a hostname, username or absolute path.
"""
import os
import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(*args):
    """stdout of a git command run at the repo root, or None if git is missing or fails."""
    try:
        out = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def git_info() -> dict:
    """{'git_commit', 'git_branch', 'dirty'}; 'unknown' and dirty=True when git is unavailable."""
    commit = _git("rev-parse", "--short", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    status = _git("status", "--porcelain", "--", "src", "tasks", "tools")
    return {
        "git_commit": commit.strip() if commit else "unknown",
        "git_branch": branch.strip() if branch else "unknown",
        "dirty": status is None or bool(status.strip()),
    }


def _version(pkg):
    try:
        return metadata.version(pkg)
    except Exception:   # not installed, or broken metadata: provenance must never crash a run
        return "unknown"


def provenance(script, wall_s=None) -> dict:
    """The CONTRACT §6.2 provenance dict, keys in schema order."""
    return {
        "script": str(script).replace("\\", "/"),
        **git_info(),
        "dynamiqs": _version("dynamiqs"),
        "jax": _version("jax"),
        "numpy": _version("numpy"),
        "scipy": _version("scipy"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "wall_s": None if wall_s is None else float(wall_s),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
