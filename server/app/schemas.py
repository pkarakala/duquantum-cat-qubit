"""Request models for CONTRACT §3 sim endpoints. Caps are enforced after parsing."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InitKind = Literal["vacuum", "coherent", "cat_plus", "cat_minus", "fock"]


class OneModeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alpha: float = Field(ge=0)
    kappa2_scale: float = Field(default=1, ge=0)
    kappa_a_scale: float = Field(default=1, ge=0)
    n_th: float = Field(default=0, ge=0)
    eps_z_over_g2: float = 0
    eps_x_over_g2: float = 0
    N: int = Field(default=30, ge=2)
    t_end_us: float = Field(default=2, gt=0)
    n_t: int = Field(default=200, ge=2)
    init: InitKind = "vacuum"
    init_alpha: float | None = None
    init_n: int | None = Field(default=None, ge=0)
    delta_over_2pi_MHz: float = 0
    outputs: list[str] = Field(min_length=1)
    wigner_times: list[float] | None = None
    learner_id: str | None = None
    level_id: str | None = None


class TwoModeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    alpha: float = Field(ge=0)
    g2_scale: float = Field(default=1, ge=0)
    kappa_b_scale: float = Field(default=1, ge=0)
    kappa_a_scale: float = Field(default=1, ge=0)
    n_th: float = Field(default=0, ge=0)
    eps_z_over_g2: float = 0
    eps_x_over_g2: float = 0
    Na: int = Field(default=16, ge=2)
    Nb: int = Field(default=5, ge=2)
    t_end_us: float = Field(default=2, gt=0)
    init: InitKind = "vacuum"
    init_alpha: float | None = None
    init_n: int | None = Field(default=None, ge=0)
    outputs: list[str] = Field(min_length=1)
    wigner_times: list[float] | None = None
    learner_id: str | None = None
    level_id: str | None = None


class ExprRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    H: dict
    jumps: list[dict] = Field(default_factory=list)
    params: dict[str, float] = Field(default_factory=dict)
    modes: Literal["one", "two"]
    N: int | None = Field(default=None, ge=2)
    Na: int | None = Field(default=None, ge=2)
    Nb: int | None = Field(default=None, ge=2)
    init: InitKind = "vacuum"
    init_alpha: float | None = None
    init_n: int | None = Field(default=None, ge=0)
    t_end_us: float = Field(gt=0)
    n_t: int = Field(default=200, ge=2)
    outputs: list[str] = Field(min_length=1)
    wigner_times: list[float] | None = None
    alpha: float | None = Field(default=None, ge=0)
    learner_id: str | None = None
    level_id: str | None = None


class RunRow(BaseModel):
    """A sim_runs row. Sims post this internally; P5 owns the hypertable."""
    model_config = ConfigDict(extra="allow")
    model: str
    params_hash: str
    engine: str = "dynamiqs 0.3.7"
    params: dict = Field(default_factory=dict)
    learner_id: str | None = None
    level_id: str | None = None
    alpha: float | None = None
    kappa2_scale: float | None = None
    eps_z_over_g2: float | None = None
    na_final: float | None = None
    wall_ms: int | None = None
    cached: bool = False
