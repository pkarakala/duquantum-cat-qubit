"""Environment for the Academy API.

Gemini, ElevenLabs, Tiger Data, and Backboard are live when their keys are set.
Backboard with no key uses the labeled demo adapter. Vultr is live when the
compose file sets VULTR_HOSTED=1. Solana stays in demo mode.
"""
import os
from pathlib import Path

ENGINE = "dynamiqs 0.3.7"
APP_VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "server" / ".env"

# Sponsors that are allowed to run in demo mode. The other three are live or off.
DEMO_SPONSORS = ("vultr", "solana", "backboard")
BACKBOARD_BASE_URL = "https://app.backboard.io/api"
SOLANA_RPC_DEFAULT = "https://api.devnet.solana.com"


def load_local_env() -> None:
    """Load server/.env without overriding variables already in the process."""
    if os.environ.get("ACADEMY_SKIP_DOTENV") == "1":
        return
    if not ENV_PATH.is_file():
        return
    for raw in ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _present(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def feature_flags() -> dict:
    """Live features follow env keys. Chain is a probe, not a key (CONTRACT §2)."""
    return {
        "gemini": _present("GEMINI_API_KEY"),
        "elevenlabs": _present("ELEVENLABS_API_KEY"),
        "backboard": _present("BACKBOARD_API_KEY"),
        "tiger": _present("TIGER_DATABASE_URL"),
        "chain": False,
    }


def integration_modes() -> dict:
    """gemini / elevenlabs / tiger are live or off. The other three are demo."""
    flags = feature_flags()
    return {
        "gemini": "live" if flags["gemini"] else "off",
        "elevenlabs": "live" if flags["elevenlabs"] else "off",
        "tiger": "live" if flags["tiger"] else "off",
        "vultr": "live" if os.environ.get("VULTR_HOSTED") == "1" else "demo",
        "solana": "demo",
        "backboard": "live" if flags["backboard"] else "demo",
    }


def demo_sponsors() -> list[str]:
    modes = integration_modes()
    return [name for name in DEMO_SPONSORS if modes[name] == "demo"]


def timeout_one_mode_s() -> float:
    # A cold one-mode compile exceeds 8s. 15s is the cap; SIM_TIMEOUT_ONE_MODE_S still overrides.
    return float(os.environ.get("SIM_TIMEOUT_ONE_MODE_S", "15"))


def timeout_two_mode_s() -> float:
    return float(os.environ.get("SIM_TIMEOUT_TWO_MODE_S", "15"))
