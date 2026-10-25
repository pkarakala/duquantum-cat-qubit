"""Test defaults: no secrets, no warmup, no outbound calls."""
import os

os.environ["ACADEMY_SKIP_DOTENV"] = "1"
os.environ["ACADEMY_WARMUP"] = "0"
os.environ["ACADEMY_SKIP_CHAIN"] = "1"
os.environ["ACADEMY_SKIP_TIGER"] = "1"
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl-academy")
os.environ.setdefault("JAX_COMPILATION_CACHE_DIR", "/tmp/academy-jax-cache")
for _key in (
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "BACKBOARD_API_KEY",
    "TIGER_DATABASE_URL",
    "SOLANA_SECRET_KEY_B58",
):
    os.environ.pop(_key, None)

import pytest

from server.app import cache
from server.app.main import limiter, reset_demo_state


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: dynamiqs runs that take more than a few seconds")


@pytest.fixture(autouse=True)
def _isolated_state():
    cache.reset_for_tests()
    reset_demo_state()
    limiter.reset()
    yield
    cache.reset_for_tests()
    reset_demo_state()


@pytest.fixture(scope="module")
def client():
    """One app per module. create_app() registers rate limits, so rebuilding it stacks them."""
    from fastapi.testclient import TestClient
    from server.app.main import app

    with TestClient(app) as test_client:
        yield test_client
