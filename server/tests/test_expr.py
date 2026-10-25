"""ExprTree allowlist, printer fixtures, and agreement with src.model."""
import json
from pathlib import Path

import numpy as np
import pytest

from src import config as C
from src.model import two_mode
from server.app.expr import ExprError, compile_tree, to_python, validate

FIXTURES = Path(__file__).parent / "fixtures" / "expr"


def test_expr_to_python_fixtures():
    files = sorted(FIXTURES.glob("*.json"))
    assert files, "expr fixtures are missing"
    for path in files:
        payload = json.loads(path.read_text())
        assert set(payload) >= {"tree", "python"}
        assert to_python(payload["tree"]) == payload["python"]


def test_expr_allowlist(client):
    cases = {
        "symbol": json.loads((FIXTURES / "invalid_symbol.json").read_text())["tree"],
        "depth": json.loads((FIXTURES / "invalid_depth.json").read_text())["tree"],
        "pow": json.loads((FIXTURES / "invalid_pow.json").read_text())["tree"],
        "sqrt": json.loads((FIXTURES / "invalid_sqrt.json").read_text())["tree"],
        "hermitian": json.loads((FIXTURES / "invalid_nonhermitian.json").read_text())["tree"],
    }
    for name, tree in cases.items():
        response = client.post("/api/sim/expr", json={
            "H": tree,
            "jumps": [],
            "modes": "one",
            "N": 8,
            "t_end_us": 0.1,
            "n_t": 4,
            "init": "vacuum",
            "outputs": ["n"],
        })
        assert response.status_code == 422, name
        assert response.json()["error"]["code"] == "invalid_expr", name


def test_expr_matches_model():
    tree = json.loads((FIXTURES / "h_2ph.json").read_text())["tree"]
    compiled = compile_tree(tree, "two", Na=8, Nb=3)
    reference, _, _ = two_mode(8, 3, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    diff = np.asarray((reference - compiled).to_jax())
    assert np.linalg.norm(diff) < 1e-12


def test_expr_validate_accepts_h_2ph():
    tree = json.loads((FIXTURES / "h_2ph.json").read_text())["tree"]
    validate(tree, modes="two", role="H")


def test_expr_rejects_directly():
    with pytest.raises(ExprError):
        validate({"op": "sym", "name": "c"}, modes="one")


def test_expr_endpoint_runs(client):
    response = client.post("/api/sim/expr", json={
        "H": {"op": "num", "value": 0},
        "jumps": [],
        "modes": "one",
        "N": 4,
        "t_end_us": 0.05,
        "n_t": 5,
        "init": "vacuum",
        "outputs": ["n", "parity"],
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["meta"]["compiled"] == "0"
    assert len(body["n"]) == 5
    assert abs(body["n"][-1]) < 1e-9
    assert "dynamiqs" in body["meta"]["engine"]

