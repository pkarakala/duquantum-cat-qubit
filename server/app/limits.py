"""Live sim caps from CONTRACT §3. Bigger jobs are precomputed, not served."""

ONE_MODE_OUTPUTS = {"n", "parity", "re_a", "wigner"}
TWO_MODE_OUTPUTS = {"na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity", "wigner"}
TWO_MODE_N_T = 201


class TooLarge(Exception):
    """The request is over a live cap. The API maps this to 413 too_large."""


class SimInputError(Exception):
    """A sim request is structurally wrong, but it is not an ExprTree."""


def check_one_mode(N: int, t_end_us: float, n_t: int) -> None:
    if N > 40:
        raise TooLarge(f"N={N} exceeds the one-mode cap N<=40")
    if t_end_us > 5:
        raise TooLarge(f"t_end_us={t_end_us} exceeds the one-mode cap of 5 µs")
    if n_t > 400:
        raise TooLarge(f"n_t={n_t} exceeds the one-mode cap n_t<=400")


def check_two_mode(Na: int, Nb: int, t_end_us: float) -> None:
    if Na > 20:
        raise TooLarge(f"Na={Na} exceeds the live cap Na<=20")
    if Nb > 6:
        raise TooLarge(f"Nb={Nb} exceeds the live cap Nb<=6")
    if t_end_us > 3:
        raise TooLarge(f"t_end_us={t_end_us} exceeds the two-mode cap of 3 µs")


def check_outputs(outputs: list[str], allowed: set[str]) -> None:
    unknown = [name for name in outputs if name not in allowed]
    if unknown:
        raise SimInputError(f"unknown outputs {unknown}; allowed {sorted(allowed)}")


def check_wigner_times(times: list[float] | None, t_end_us: float) -> None:
    if not times:
        return
    for t in times:
        if t < 0 or t > t_end_us + 1e-9:
            raise SimInputError(f"wigner time {t} is outside [0, {t_end_us}]")
