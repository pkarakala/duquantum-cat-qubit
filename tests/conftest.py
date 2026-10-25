"""Shared pytest setup: repo root on sys.path, and double precision before any array exists."""
import sys
from pathlib import Path

import matplotlib

# Tests never show windows; the macOS GUI backend aborts the interpreter when a figure is
# created without a window server, so pin the file-only backend before pyplot is imported.
matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config  # noqa: F401,E402  (sets jax_enable_x64; must precede every array)
