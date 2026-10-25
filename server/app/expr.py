"""ExprTree validator, dynamiqs compiler, and the shared to_python printer.

The printer is the contract P3's TypeScript port must match exactly:
integers have no decimal, other reals use the shortest round-trip form and
never an exponent, a pure imaginary is `1j`, products of operators use `@`,
scalar products use `*`, powers are expanded, and sums use ` + ` / ` - `.
"""
import numpy as np

from src import config as C
import dynamiqs as dq

class ExprError(ValueError):
    """The tree is outside the allowlist. The API maps this to 422 invalid_expr."""


_OPS = {"num", "param", "sym", "add", "mul", "pow", "dag", "sqrt"}
_PARAMS = {"g2", "eps_d", "kappa_b", "kappa_a", "kappa2", "alpha", "eps_z", "eps_x", "K", "chi"}
_SYMS_ONE = {"a", "ad", "I", "n_a"}
_SYMS_TWO = _SYMS_ONE | {"b", "bd"}
_SYM_PY = {
    "a": "a",
    "ad": "a.dag()",
    "b": "b",
    "bd": "b.dag()",
    "I": "dq.eye(N)",
    "n_a": "a.dag()@a",
}


def _children(tree: dict) -> list:
    op = tree.get("op")
    if op in ("add", "mul"):
        return list(tree.get("args") or [])
    if op in ("dag", "sqrt"):
        arg = tree.get("arg")
        return [arg] if isinstance(arg, dict) else []
    if op == "pow":
        base = tree.get("base")
        return [base] if isinstance(base, dict) else []
    return []


def _as_int_exp(exp):
    if isinstance(exp, bool) or exp is None:
        return None
    if isinstance(exp, int):
        return exp
    if isinstance(exp, float) and exp.is_integer():
        return int(exp)
    return None


def _walk(tree, modes: str, box: dict, depth: int) -> None:
    if not isinstance(tree, dict) or "op" not in tree:
        raise ExprError("expression node must be an object with op")
    box["nodes"] += 1
    if box["nodes"] > 64:
        raise ExprError("expression has more than 64 nodes")
    if depth > 8:
        raise ExprError("expression depth exceeds 8")
    op = tree["op"]
    if op not in _OPS:
        raise ExprError(f"unknown op {op}")
    allowed = _SYMS_TWO if modes == "two" else _SYMS_ONE
    if op == "sym" and tree.get("name") not in allowed:
        raise ExprError(f"unknown symbol {tree.get('name')}")
    elif op == "param" and tree.get("name") not in _PARAMS:
        raise ExprError(f"unknown param {tree.get('name')}")
    elif op == "num":
        value = tree.get("value")
        imag = tree.get("imag", 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ExprError("num value must be real")
        if isinstance(imag, bool) or not isinstance(imag, (int, float)):
            raise ExprError("num imag must be real")
    elif op == "pow":
        exp = _as_int_exp(tree.get("exp"))
        if exp is None or not 0 <= exp <= 4:
            raise ExprError("pow exp must be an integer from 0 to 4")
    elif op == "sqrt":
        arg = tree.get("arg")
        if not isinstance(arg, dict) or arg.get("op") not in ("param", "num"):
            raise ExprError("sqrt only applies to a param or a num")
    elif op in ("add", "mul"):
        args = tree.get("args")
        if not isinstance(args, list) or not args:
            raise ExprError(f"{op} needs at least one argument")
    for kid in _children(tree):
        _walk(kid, modes, box, depth + 1)


def resolve_params(overrides: dict | None) -> dict:
    """Config rates, overridden by the request. Values are rad/µs."""
    out = {
        "g2": float(C.G2),
        "eps_d": float(C.EPS_D),
        "kappa_b": float(C.KAPPA_B),
        "kappa_a": float(C.KAPPA_A),
        "kappa2": float(C.KAPPA_2),
        "alpha": float(C.ALPHA),
    }
    for name, value in (overrides or {}).items():
        if name not in _PARAMS:
            raise ExprError(f"unknown param {name}")
        out[name] = float(value)
    return out


def _basis(modes: str, N: int | None, Na: int | None, Nb: int | None) -> dict:
    if modes == "one":
        if N is None:
            raise ExprError("one-mode expression needs N")
        a = dq.destroy(int(N))
        return {"a": a, "ad": a.dag(), "I": dq.eye(int(N)), "n_a": a.dag() @ a}
    if Na is None or Nb is None:
        raise ExprError("two-mode expression needs Na and Nb")
    a, b = dq.destroy(int(Na), int(Nb))
    return {
        "a": a,
        "ad": a.dag(),
        "b": b,
        "bd": b.dag(),
        "I": dq.eye(int(Na), int(Nb)),
        "n_a": a.dag() @ a,
    }


def _eval(tree: dict, ops: dict, params: dict):
    op = tree["op"]
    if op == "num":
        return complex(float(tree["value"]), float(tree.get("imag") or 0))
    if op == "param":
        name = tree["name"]
        if name not in params:
            raise ExprError(f"unknown param {name}")
        return params[name]
    if op == "sym":
        name = tree["name"]
        if name not in ops:
            raise ExprError(f"unknown symbol {name}")
        return ops[name]
    if op == "add":
        acc = _eval(tree["args"][0], ops, params)
        for arg in tree["args"][1:]:
            acc = acc + _eval(arg, ops, params)
        return acc
    if op == "mul":
        acc = _eval(tree["args"][0], ops, params)
        for arg in tree["args"][1:]:
            acc = _mul(acc, _eval(arg, ops, params))
        return acc
    if op == "pow":
        return _pow(_eval(tree["base"], ops, params), _as_int_exp(tree.get("exp")))
    if op == "dag":
        val = _eval(tree["arg"], ops, params)
        return val.dag() if isinstance(val, dq.QArray) else complex(val).conjugate()
    if op == "sqrt":
        val = _eval(tree["arg"], ops, params)
        if isinstance(val, dq.QArray):
            raise ExprError("sqrt only applies to a param or a num")
        return float(np.sqrt(val))
    raise ExprError(f"unknown op {op}")


def _mul(left, right):
    if isinstance(left, dq.QArray) and isinstance(right, dq.QArray):
        return left @ right
    return left * right


def _pow(base, exp):
    if exp is None or not 0 <= exp <= 4:
        raise ExprError("pow exp must be an integer from 0 to 4")
    if exp == 0:
        if isinstance(base, dq.QArray):
            return dq.eye(int(base.shape[-1]))
        return 1.0
    acc = base
    for _ in range(exp - 1):
        acc = acc @ base if isinstance(base, dq.QArray) else acc * base
    return acc


def compile_tree(tree: dict, modes: str, N: int | None = None, Na: int | None = None,
                 Nb: int | None = None, params: dict | None = None):
    """Compile an ExprTree to a dynamiqs QArray (or a scalar for a pure number)."""
    return _eval(tree, _basis(modes, N, Na, Nb), resolve_params(params))


def is_hermitian(H, tol: float = 1e-9) -> bool:
    if isinstance(H, (int, float, complex)):
        return abs(complex(H).imag) <= tol
    diff = H - H.dag()
    arr = np.asarray(diff.to_jax() if hasattr(diff, "to_jax") else diff)
    return float(np.max(np.abs(arr))) <= tol


def validate(tree: dict, modes: str = "one", params: dict | None = None, role: str = "H") -> None:
    """Allowlist, depth, node count, and (for H) hermiticity at a small truncation."""
    _walk(tree, modes, {"nodes": 0}, 1)
    if role != "H":
        return
    if modes == "one":
        compiled = compile_tree(tree, "one", N=8, params=params)
    else:
        compiled = compile_tree(tree, "two", Na=4, Nb=3, params=params)
    if not is_hermitian(compiled):
        raise ExprError("H is not Hermitian")


def _fmt_real(value: float) -> str:
    if abs(value - round(value)) < 1e-12 and abs(value) < 1e15:
        return str(int(round(value)))
    text = format(float(value), ".12g")
    if "e" in text or "E" in text:
        text = f"{float(value):.10f}".rstrip("0").rstrip(".")
    return text


def _fmt_complex(real: float, imag: float) -> str:
    if abs(imag) < 1e-15:
        return _fmt_real(real)
    if abs(real) < 1e-15:
        if abs(imag - 1) < 1e-15:
            return "1j"
        if abs(imag + 1) < 1e-15:
            return "-1j"
        return f"{_fmt_real(imag)}j"
    sign = "+" if imag > 0 else "-"
    return f"({_fmt_real(real)}{sign}{_fmt_real(abs(imag))}j)"


def _is_scalar_tree(tree: dict) -> bool:
    op = tree.get("op")
    if op in ("num", "param", "sqrt"):
        return True
    if op == "sym":
        return False
    if op == "dag":
        return _is_scalar_tree(tree["arg"])
    if op == "pow":
        return _is_scalar_tree(tree["base"])
    if op in ("add", "mul"):
        return all(_is_scalar_tree(arg) for arg in tree.get("args") or [])
    return False


def _split_minus(tree: dict):
    """Pull a leading real minus out of a num or a mul, for ` + ` / ` - ` joins."""
    if tree.get("op") == "num":
        imag = float(tree.get("imag") or 0)
        value = float(tree["value"])
        if abs(imag) < 1e-15 and value < 0:
            return True, {"op": "num", "value": -value}
        return False, tree
    if tree.get("op") != "mul":
        return False, tree
    args = list(tree.get("args") or [])
    if not args or args[0].get("op") != "num":
        return False, tree
    imag = float(args[0].get("imag") or 0)
    value = float(args[0]["value"])
    if abs(imag) >= 1e-15 or value >= 0:
        return False, tree
    if abs(value + 1) < 1e-12 and len(args) > 1:
        rest = args[1:]
        return True, rest[0] if len(rest) == 1 else {"op": "mul", "args": rest}
    flipped = {"op": "num", "value": -value}
    return True, {"op": "mul", "args": [flipped, *args[1:]]}


def fmt_node(tree: dict, parent: str | None = None) -> str:
    text = _fmt(tree)
    if tree.get("op") == "add" and parent in ("mul", "pow", "dag", "sqrt"):
        return f"({text})"
    return text


def _fmt(tree: dict) -> str:
    op = tree.get("op")
    if op == "num":
        return _fmt_complex(float(tree["value"]), float(tree.get("imag") or 0))
    if op == "param":
        return str(tree["name"])
    if op == "sym":
        return _SYM_PY.get(tree.get("name"), str(tree.get("name")))
    if op == "add":
        return _fmt_add(tree["args"])
    if op == "mul":
        return _fmt_mul(tree["args"])
    if op == "pow":
        return _fmt_pow(tree)
    if op == "dag":
        return _fmt_dag(tree["arg"])
    if op == "sqrt":
        return f"jnp.sqrt({fmt_node(tree['arg'], parent='sqrt')})"
    raise ExprError(f"unknown op {op}")


def _fmt_add(args: list) -> str:
    chunks = []
    for index, arg in enumerate(args):
        neg, body = _split_minus(arg)
        text = fmt_node(body, parent="add")
        if index == 0:
            chunks.append(("-" + text) if neg else text)
        else:
            chunks.append((" - " if neg else " + ") + text)
    return "".join(chunks)


def _fmt_mul(args: list) -> str:
    neg, body = _split_minus({"op": "mul", "args": args})
    if not neg:
        return _fmt_mul_body(args)
    if isinstance(body, dict) and body.get("op") == "mul":
        return "-" + _fmt_mul_body(body["args"])
    return "-" + fmt_node(body, parent="mul")


def _fmt_mul_body(args: list) -> str:
    parts = []
    acc_op = False
    for index, arg in enumerate(args):
        text = fmt_node(arg, parent="mul")
        arg_op = not _is_scalar_tree(arg)
        if index == 0:
            parts.append(text)
        else:
            parts.append(("@" if acc_op and arg_op else "*") + text)
        acc_op = acc_op or arg_op
    return "".join(parts)


def _fmt_pow(tree: dict) -> str:
    base = tree["base"]
    exp = _as_int_exp(tree.get("exp"))
    if exp is None:
        return f"({fmt_node(base, parent='pow')})**{tree.get('exp')}"
    if exp == 0:
        return "1" if _is_scalar_tree(base) else "dq.eye(N)"
    atom = fmt_node(base, parent="pow")
    if exp == 1:
        return atom
    if base.get("op") in ("add", "mul") and not atom.startswith("("):
        atom = f"({atom})"
    joiner = "*" if _is_scalar_tree(base) else "@"
    return joiner.join([atom] * exp)


def _fmt_dag(arg: dict) -> str:
    if arg.get("op") == "sym" and arg.get("name") == "a":
        return "a.dag()"
    if arg.get("op") == "sym" and arg.get("name") == "b":
        return "b.dag()"
    inner = fmt_node(arg, parent="dag")
    if arg.get("op") in ("sym", "dag", "param", "num"):
        return f"{inner}.dag()"
    return f"({inner}).dag()"


def to_python(tree: dict) -> str:
    """Dynamiqs snippet. Must match server/tests/fixtures/expr/*.json exactly."""
    return fmt_node(tree)
