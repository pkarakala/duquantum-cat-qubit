// Deterministic MOCK data for the Lab, in the exact CONTRACT §13 shapes (brief 11 §6 step 3).
// Every number here is a synthetic placeholder from closed forms (RESEARCH §1, §5-§7), never a result:
// record ids start with "mock.", git_commit is "mock", and the site shows a MOCK DATA banner.
// This file and tools/export_lab_data.py are the only places where formulas live; the browser only plots.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// rad/us, as in src/config.py (the 2*pi is the MHz -> rad/us conversion of the nominal parameters).
const MHZ = 2 * Math.PI;
const G2 = MHZ * 0.763;
const KAPPA_B = MHZ * 2.6;
const KAPPA_A = MHZ * 9.3e-3;
const KAPPA_2 = (4 * G2 * G2) / KAPPA_B;
const ALPHA = 2.1;
const SIGMA = KAPPA_B / 4;

const MOCK_NOTE = "MOCK: synthetic placeholder, not a result";

// ---- numeric helpers (deterministic; -0 normalised so JSON round-trips compare equal) ----
const nz = (v) => (Object.is(v, -0) ? 0 : v);
const sig = (x, n = 6) => (x === 0 ? 0 : nz(Number(x.toPrecision(n))));
const dec = (x, d = 4) => nz(Number(x.toFixed(d)));
const linspace = (a, b, n) => Array.from({ length: n }, (_, i) => a + ((b - a) * i) / (n - 1));
const grid01 = (lo, hi) => Array.from({ length: Math.round((hi - lo) * 10) + 1 }, (_, i) => Math.round(lo * 10 + i) / 10);
const coth = (x) => Math.cosh(x) / Math.sinh(x);
const aTag = (alpha) => `a${alpha.toFixed(2)}`;
const gTag = (x) => String(Number(x.toPrecision(3)));

function trapz(t, y) {
  let s = 0;
  for (let i = 1; i < t.length; i++) s += 0.5 * (t[i] - t[i - 1]) * (y[i] + y[i - 1]);
  return s;
}

// Under-damped second-order step response 1 - e^{-sigma t}(cos wt + (sigma/w) sin wt), w from RESEARCH §7.
function omegaD(alpha) {
  return Math.sqrt(4 * G2 * G2 * alpha * alpha - SIGMA * SIGMA);
}
function stepResponse(t, alpha) {
  const w = omegaD(alpha);
  return 1 - Math.exp(-SIGMA * t) * (Math.cos(w * t) + (SIGMA / w) * Math.sin(w * t));
}

// Gamma_X channels (RESEARCH §5): ch1 = kappa_a a^2 (coth 2a^2 - 1), ch2 = (kappa_a^2/kappa_2) e^{-2a^2}.
const ch1 = (a2) => KAPPA_A * a2 * (coth(2 * a2) - 1);
const ch2 = (a2) => ((KAPPA_A * KAPPA_A) / KAPPA_2) * Math.exp(-2 * a2);
const gammaZ = (a2) => 2 * KAPPA_A * a2 * coth(2 * a2);
const oneMode = (alpha) => ch1(alpha * alpha) + 1.3 * ch2(alpha * alpha);
// Two-mode / one-mode factor, log-interpolated through the RESEARCH §5 anchors (linear extrapolation in log).
const FACTOR_KNOTS = [
  [1.0, 1.01],
  [1.4, 1.12],
  [1.8, 2.0],
  [2.1, 3.0],
];
function twoModeFactor(alpha) {
  const k = FACTOR_KNOTS;
  let i = 0;
  while (i < k.length - 2 && alpha > k[i + 1][0]) i++;
  const [x0, f0] = k[i];
  const [x1, f1] = k[i + 1];
  const lf = Math.log(f0) + ((Math.log(f1) - Math.log(f0)) * (alpha - x0)) / (x1 - x0);
  return Math.max(1, Math.exp(lf));
}
const twoMode = (alpha) => oneMode(alpha) * twoModeFactor(alpha);

// ---- mock record builders ----
function stdParams(alpha, extra = {}) {
  return {
    g2_MHz: 0.763,
    kappa_b_MHz: 2.6,
    kappa_a_kHz: 9.3,
    alpha,
    n_th: 0,
    eps_z_over_g2: 0,
    eps_x_over_g2: 0,
    ...extra,
  };
}

function xc(method, value, ref, tol, refId = null) {
  const relDiff = sig(Math.abs(value - ref) / Math.abs(ref), 4);
  return { method, ref_id: refId, value: sig(ref), rel_diff: relDiff, tol, agree: relDiff <= tol };
}

// Synthetic Na/Nb sweeps that settle on `value` (converged) or keep drifting (not converged).
// One-mode truncations (Nb = 1) sweep Na only.
function conv(key, value, trunc, { relTol = 1e-3, converged = true } = {}) {
  const drift = converged ? 1e-5 : 2e-2;
  const sweeps = {
    Na: { fixed: { Nb: trunc.Nb }, values: [trunc.Na - 8, trunc.Na - 4, trunc.Na], results: [value * (1 + 5e-3), value * (1 + drift), value].map((v) => sig(v)) },
  };
  const needed = { Na: converged ? trunc.Na - 4 : null };
  if (trunc.Nb > 1) {
    sweeps.Nb = { fixed: { Na: trunc.Na }, values: [trunc.Nb - 2, trunc.Nb], results: [value * (1 + drift), value].map((v) => sig(v)) };
    needed.Nb = converged ? trunc.Nb - 2 : null;
  }
  return { key, rel_tol: relTol, sweeps, needed, converged };
}

function rec({ id, task, quantity, value, unc = null, units, method, params, truncation = null, convergence = null, cross_check = [], numerics = null, script }) {
  return {
    schema: "duq.record/v2",
    id: `mock.${id}`,
    task,
    quantity,
    value: sig(value),
    uncertainty: unc === null ? null : sig(unc, 2),
    units,
    method,
    params,
    truncation,
    convergence,
    numerics,
    cross_check,
    artifacts: null,
    notes: MOCK_NOTE,
    provenance: {
      script,
      git_commit: "mock",
      git_branch: "mock",
      dirty: false,
      dynamiqs: "0.3.7",
      jax: "0.12.0.1",
      numpy: null,
      scipy: null,
      python: null,
      platform: "mock",
      cpu_count: null,
      wall_s: null,
      timestamp: "MOCK",
      generator: "site/scripts/make_mock.mjs",
    },
  };
}

// ---- inflation ----
const FRAME_TIMES = [...Array.from({ length: 26 }, (_, i) => i * 0.02), ...Array.from({ length: 13 }, (_, i) => 0.6 + i * 0.2)].map((t) => dec(t, 2));

function evenCatWigner(beta, xs, ys) {
  const n2 = 1 / (2 * (1 + Math.exp(-2 * beta * beta)));
  return ys.map((y) =>
    xs.map((x) => {
      const r = Math.exp(-2 * ((x - beta) ** 2 + y * y));
      const l = Math.exp(-2 * ((x + beta) ** 2 + y * y));
      const c = 2 * Math.exp(-2 * (x * x + y * y)) * Math.cos(4 * beta * y);
      return dec(n2 * (2 / Math.PI) * (r + l + c));
    }),
  );
}

function buildInflation(records) {
  const a2 = ALPHA * ALPHA;
  const naOf = (t) => a2 * stepResponse(t, ALPHA);
  const nbOf = (t) => 3.8 * Math.exp(-SIGMA * t) * Math.sin((omegaD(ALPHA) * t) / 2) ** 2;
  const t = linspace(0, 3, 301);
  const na = t.map(naOf);
  const nb = t.map(nbOf);
  const xs = linspace(-4, 4, 81).map((v) => dec(v, 6));
  const frames = FRAME_TIMES.map((tf) => ({ t_us: tf, w: evenCatWigner(Math.sqrt(Math.max(naOf(tf), 0)), xs, xs) }));

  const peakNa = Math.max(...na);
  const peakNb = Math.max(...nb);
  let settle = 0;
  na.forEach((v, i) => {
    if (Math.abs(v / a2 - 1) > 0.01) settle = t[i];
  });
  const tr = { Na: 32, Nb: 12 };
  const p = stdParams(ALPHA);
  const script = "tasks/task_1_1.py";
  records.push(
    rec({ id: "t1_1.peak_na.td.two_mode.a2.10", task: "1.1", quantity: "peak_na", value: peakNa, units: "photons", method: "mesolve_peak", params: p, truncation: tr, convergence: conv("peak_na", peakNa, tr, { relTol: 0.005 }), cross_check: [xc("larger_truncation_same_solver", peakNa, peakNa * 1.0003, 0.005)], script }),
    rec({ id: "t1_1.steady_na.td.two_mode.a2.10", task: "1.1", quantity: "steady_na", value: na[na.length - 1], units: "photons", method: "mesolve_final_value", params: p, truncation: tr, convergence: conv("steady_na", na[na.length - 1], tr), cross_check: [xc("alpha_squared", na[na.length - 1], a2, 0.01)], script }),
    rec({ id: "t1_1.peak_nb.td.two_mode.a2.10", task: "1.1", quantity: "peak_nb", value: peakNb, units: "photons", method: "mesolve_peak", params: p, truncation: tr, convergence: conv("peak_nb", peakNb, tr, { relTol: 0.005 }), cross_check: [xc("larger_truncation_same_solver", peakNb, peakNb * 1.00002, 0.005)], script }),
    rec({ id: "t1_1.settle_1pct.td.two_mode.a2.10", task: "1.1", quantity: "settle_1pct", value: settle, units: "us", method: "mesolve_settle", params: p, truncation: tr, convergence: null, cross_check: [xc("linresp_analytic", settle, 1.13, 0.1)], script }),
  );

  return {
    t_us: t.map((v) => sig(v)),
    na: na.map((v) => sig(v)),
    nb: nb.map((v) => sig(v)),
    top2_a: na.map((v) => sig(1e-9 * (v / a2) ** 4 + 1e-14)),
    top_b: nb.map((v) => sig(1e-8 * v * v + 1e-14)),
    effective: { t_us: t.map((v) => sig(v)), na: t.map((v) => sig(a2 * (1 - Math.exp(-2 * KAPPA_2 * a2 * v)))) },
    wigner: { x: xs, y: xs, frames },
    record_ids: ["peak_na", "steady_na", "peak_nb", "settle_1pct"].map((q) => `mock.t1_1.${q}.td.two_mode.a2.10`).sort(),
    alpha: ALPHA,
  };
}

// ---- errors ----
function localSlope(series) {
  // -d ln(Gamma)/d(alpha^2) by adjacent finite differences, placed at midpoints, on the union grid.
  const mids = new Map();
  const perModel = {};
  for (const [model, pts] of Object.entries(series)) {
    perModel[model] = new Map();
    for (let i = 0; i + 1 < pts.length; i++) {
      const [x0, y0] = pts[i];
      const [x1, y1] = pts[i + 1];
      const m = sig((x0 + x1) / 2);
      mids.set(m, true);
      perModel[model].set(m, sig(-(Math.log(y1) - Math.log(y0)) / (x1 - x0)));
    }
  }
  const alpha2 = [...mids.keys()].sort((a, b) => a - b);
  const out = { alpha2 };
  for (const model of Object.keys(series)) out[model] = alpha2.map((m) => (perModel[model].has(m) ? perModel[model].get(m) : null));
  return out;
}

function buildErrors(records) {
  const eigScript = "tasks/task_2_1_eig.py";
  const point = (r, alpha, extra = {}) => ({ alpha2: sig(alpha * alpha), value: r.value, unc: r.uncertainty, id: r.id, ...extra });
  const oneModePts = [];
  const twoModePts = [];
  const tdPts = [];
  const thermal = {};

  for (const alpha of grid01(0.8, 2.7)) {
    const v = oneMode(alpha);
    const a2 = alpha * alpha;
    const N = Math.max(20, 2 * Math.ceil((a2 + 6 * alpha + 14) / 2));
    const r = rec({
      id: `t2_1.gamma_x.eig.one_mode.${aTag(alpha)}.nth0`, task: "2.1", quantity: "gamma_x", value: v, unc: v * 1e-6, units: "1/us",
      method: "liouvillian_eig_odd_sector", params: stdParams(alpha), truncation: { Na: N, Nb: 1 },
      convergence: conv("gamma_x", v, { Na: N, Nb: 1 }),
      numerics: { rel_residual: 3e-9, edge_weight: 1e-12, cond_est: 50, sector: "odd", sigma: 0, k: 2 },
      cross_check: [xc("analytic_channels", v, ch1(a2) + ch2(a2), 0.35)], script: eigScript,
    });
    records.push(r);
    oneModePts.push(point(r, alpha));
  }

  for (const alpha of grid01(0.8, 2.4)) {
    const v = twoMode(alpha);
    const tr = { Na: Math.max(20, 2 * Math.ceil((alpha * alpha + 6 * alpha + 12) / 2)), Nb: 8 };
    const amber = Math.abs(alpha - 2.4) < 1e-9; // deliberately unconverged, to show an amber card
    const r = rec({
      id: `t2_1.gamma_x.eig.two_mode.${aTag(alpha)}.nth0`, task: "2.1", quantity: "gamma_x", value: v, unc: v * 1e-5, units: "1/us",
      method: "liouvillian_eig_odd_sector", params: stdParams(alpha), truncation: tr, convergence: conv("gamma_x", v, tr, { converged: !amber }),
      numerics: { rel_residual: 2e-8, edge_weight: amber ? 4e-6 : 1e-9, cond_est: 120, sector: "odd", sigma: 0, k: 2 },
      cross_check: [xc("full_liouvillian_shift_invert", v, v * (1 + 3e-7), 1e-4)], script: eigScript,
    });
    records.push(r);
    twoModePts.push(point(r, alpha));
  }

  for (const model of ["one_mode", "two_mode"]) {
    for (const alpha of [0.8, 1.0, 1.2, 1.4]) {
      const eig = model === "one_mode" ? oneMode(alpha) : twoMode(alpha);
      const v = eig * 1.006;
      const eigId = `mock.t2_1.gamma_x.eig.${model}.${aTag(alpha)}.nth0`;
      const tr = model === "one_mode" ? { Na: 24, Nb: 1 } : { Na: 20, Nb: 6 };
      const r = rec({
        id: `t2_1.gamma_x.td.${model}.${aTag(alpha)}`, task: "2.1", quantity: "gamma_x", value: v, unc: v * 0.01, units: "1/us",
        method: "time_domain_fit_re_a", params: stdParams(alpha), truncation: tr, convergence: conv("gamma_x", v, tr),
        numerics: { fit_window_us: [3, 80], gamma_stderr: v * 0.01, rel_rms_residual: 2e-4 },
        cross_check: [xc("liouvillian_eig", v, eig, 0.02, eigId)], script: "tasks/task_2_1_td.py",
      });
      records.push(r);
      tdPts.push(point(r, alpha, { model }));
    }
  }

  for (const nth of [0.01, 0.03, 0.05]) {
    const key = String(nth);
    thermal[key] = [];
    for (const alpha of grid01(0.8, 2.7)) {
      const a2 = alpha * alpha;
      const add = KAPPA_A * nth * Math.exp(-2 * a2);
      const v = oneMode(alpha) + add;
      const r = rec({
        id: `t2_1.gamma_x.eig.one_mode.${aTag(alpha)}.nth${key}`, task: "2.1", quantity: "gamma_x", value: v, unc: v * 1e-6, units: "1/us",
        method: "liouvillian_eig_odd_sector", params: stdParams(alpha, { n_th: nth }), truncation: { Na: 40, Nb: 1 },
        convergence: conv("gamma_x", v, { Na: 40, Nb: 1 }), numerics: { rel_residual: 3e-9, edge_weight: 1e-12, cond_est: 50, sector: "odd", sigma: 0, k: 2 },
        cross_check: [xc("analytic_thermal_gautier_eq4", v, ch1(a2) + ch2(a2) + add, 0.35)], script: "tasks/task_2_1_thermal.py",
      });
      records.push(r);
      thermal[key].push(point(r, alpha));
    }
  }

  const a2grid = linspace(0.5, 9, 200);
  const analytic = {
    alpha2: a2grid.map((v) => sig(v)),
    ch1: a2grid.map((v) => sig(ch1(v))),
    ch2: a2grid.map((v) => sig(ch2(v))),
    total: a2grid.map((v) => sig(ch1(v) + ch2(v))),
    source: "mock_closed_form_RESEARCH_5",
  };

  const gzTd = [];
  const gzEig = [];
  const pred = { alpha2: [], value: [] };
  for (const alpha of [1.0, 1.4, 1.8, 2.1, 2.4, 2.7]) {
    const a2 = alpha * alpha;
    const p = gammaZ(a2);
    const tdV = p * (1 - 0.003);
    const eigV = p * (1 + 0.0005);
    const tdId = `mock.t2_2.gamma_z.td.two_mode.${aTag(alpha)}`;
    const eigId = `mock.t2_2.gamma_z.eig.two_mode.${aTag(alpha)}`;
    const tr = { Na: 2 * Math.ceil((a2 + 6 * alpha + 14) / 2), Nb: 8 };
    const td = rec({
      id: `t2_2.gamma_z.td.two_mode.${aTag(alpha)}`, task: "2.2", quantity: "gamma_z", value: tdV, unc: tdV * 0.002, units: "1/us",
      method: "time_domain_fit_exp_offset", params: stdParams(alpha), truncation: tr, convergence: conv("gamma_z", tdV, tr),
      numerics: { fit_window_us: [0, 1 / p], gamma_stderr: tdV * 0.002, rel_rms_residual: 1e-4, C_pred: sig(1 / Math.cosh(2 * a2)) },
      cross_check: [xc("analytic_coth", tdV, p, 0.02), xc("liouvillian_eig_even", tdV, eigV, 0.01, eigId)], script: "tasks/task_2_2.py",
    });
    const eig = rec({
      id: `t2_2.gamma_z.eig.two_mode.${aTag(alpha)}`, task: "2.2", quantity: "gamma_z", value: eigV, unc: null, units: "1/us",
      method: "liouvillian_eig_even_sector", params: stdParams(alpha), truncation: tr, convergence: conv("gamma_z", eigV, tr),
      numerics: { rel_residual: 1e-9, edge_weight: 1e-10, cond_est: 30, sector: "even", sigma: 0, k: 4 },
      cross_check: [xc("analytic_coth", eigV, p, 0.02), xc("time_domain_fit", eigV, tdV, 0.01, tdId)], script: "tasks/task_2_2.py",
    });
    records.push(td, eig);
    gzTd.push(point(td, alpha));
    gzEig.push(point(eig, alpha));
    pred.alpha2.push(sig(a2));
    pred.value.push(td.cross_check[0].value);
  }

  return {
    gamma_x: {
      one_mode: oneModePts,
      two_mode: twoModePts,
      td: tdPts,
      analytic,
      thermal,
      thermal_model: "one_mode",
      local_slope: {
        ...localSlope({
          one_mode: oneModePts.map((p) => [p.alpha2, p.value]),
          two_mode: twoModePts.map((p) => [p.alpha2, p.value]),
        }),
        source: "finite_difference",
      },
    },
    gamma_z: { td: gzTd, eig: gzEig, pred },
  };
}

// ---- readout ----
// Linear response about the +alpha well (RESEARCH §7), RK4 with piecewise-constant eps.
function linrespBuffer(edges, values, alpha, tEnd, dt = 1e-3) {
  const c = 2 * G2 * alpha;
  // state: delta_a = ar + i ai, b = br + i bi
  const f = (s, eps) => {
    const [ar, ai, br, bi] = s;
    // d(delta_a)/dt = -i c b - i eps ; db/dt = -i c delta_a - (kappa_b/2) b
    return [c * bi, -c * br - eps, c * ai - (KAPPA_B / 2) * br, -c * ar - (KAPPA_B / 2) * bi];
  };
  const epsAt = (t) => {
    for (let k = 0; k < values.length; k++) if (t < edges[k + 1] - 1e-12) return t >= edges[k] - 1e-12 ? values[k] : 0;
    return 0;
  };
  let s = [0, 0, 0, 0];
  const t = [0];
  const db = [0];
  const nSteps = Math.round(tEnd / dt);
  for (let n = 0; n < nSteps; n++) {
    const t0 = n * dt;
    const eps = epsAt(t0 + dt / 2);
    const k1 = f(s, eps);
    const k2 = f(s.map((v, i) => v + (dt / 2) * k1[i]), eps);
    const k3 = f(s.map((v, i) => v + (dt / 2) * k2[i]), eps);
    const k4 = f(s.map((v, i) => v + dt * k3[i]), eps);
    s = s.map((v, i) => v + (dt / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
    t.push((n + 1) * dt);
    db.push(2 * Math.hypot(s[2], s[3])); // Delta b = b(+alpha) - b(-alpha) = 2 b
  }
  return { t, db };
}

function snrStep(epsOverG2, alpha) {
  const t = linspace(0, 1, 1001);
  const y = t.map((tt) => (2 * (epsOverG2 / (2 * alpha)) * stepResponse(tt, alpha)) ** 2);
  return KAPPA_B * trapz(t, y);
}

function buildReadout(records) {
  const epsGrid = [0.05, 0.1, 0.2, 0.5, 1, 2, 3];
  const t = linspace(0, 3, 301);
  const signalsByEps = epsGrid.map((e) => {
    const bp = t.map((tt) => -(e / (2 * ALPHA)) * stepResponse(tt, ALPHA));
    return {
      eps_over_g2: e,
      t_us: t.map((v) => sig(v)),
      b_plus_re: bp.map((v) => sig(v)),
      b_plus_im: t.map(() => -0.003),
      b_minus_re: bp.map((v) => sig(-v)),
      b_minus_im: t.map(() => -0.003),
    };
  });
  const signals = { ...signalsByEps.find((s) => s.eps_over_g2 === 1) };

  const linId = "t2_3.ring_freq.linresp.two_mode.a2.10";
  records.push(
    rec({
      id: linId, task: "2.3", quantity: "ring_freq", value: 3.14, units: "MHz", method: "linresp", params: stdParams(ALPHA), convergence: null,
      numerics: { freq_MHz: 3.14, Q: 2.46, decay_per_us: 4.08, t_settle_5pct_us: 0.73, t_settle_1pct_us: 1.13 },
      cross_check: [xc("damped_sine_fit_td", 3.14, 3.13, 0.05, "mock.t2_3.ring_freq.td.two_mode.a2.10")], script: "tasks/task_2_3.py",
    }),
  );
  records.push(
    rec({
      id: "t2_3.ring_freq.td.two_mode.a2.10", task: "2.3", quantity: "ring_freq", value: 3.13, units: "MHz", method: "damped_sine_fit",
      params: stdParams(ALPHA, { eps_z_over_g2: 0.1 }), truncation: { Na: 28, Nb: 8 }, convergence: conv("ring_freq", 3.13, { Na: 28, Nb: 8 }),
      cross_check: [xc("linresp", 3.13, 3.14, 0.05, `mock.${linId}`)], script: "tasks/task_2_3.py",
    }),
  );

  const tradeoff = [];
  for (const alpha of [1.4, 2.1]) {
    const gx0 = twoMode(alpha);
    const k = alpha === 2.1 ? 0.5 : 0.3;
    for (const e of epsGrid) {
      const rel = 1 + k * e * e;
      const id = `t2_4b.gamma_x.eig.two_mode.${aTag(alpha)}.ez${gTag(e)}g2`;
      const finding = alpha === 2.1 && e === 3; // a disagreeing overlay: amber "no agreeing cross-check"
      const overlay = gx0 * (1 + (finding ? 0.15 : 0.9 * k) * e * e);
      const tr = { Na: 32, Nb: 10 };
      records.push(
        rec({
          id, task: "2.4b", quantity: "gamma_x", value: gx0 * rel, units: "1/us", method: "liouvillian_eig_full_deflated",
          params: stdParams(alpha, { eps_z_over_g2: e }), truncation: tr, convergence: conv("gamma_x", gx0 * rel, tr),
          numerics: { rel_residual: 5e-8, edge_weight: 1e-9, cond_est: 300, sector: "full_deflated", sigma: 0, k: 4 },
          cross_check: [xc("dubovitskii_overlay", gx0 * rel, overlay, 0.3)], script: "tasks/task_2_4b.py",
        }),
      );
      tradeoff.push({ eps_over_g2: e, snr_T1us: sig(snrStep(e, alpha)), gamma_x_rel: sig(rel), id: `mock.${id}`, alpha, ok: true });
    }
  }

  const T = 1;
  const nBins = 50;
  const edges = linspace(0, T, nBins + 1).map((v) => sig(v));
  const centers = edges.slice(0, -1).map((e, i) => (e + edges[i + 1]) / 2);
  const shapes = {
    square: () => 1,
    cos_ramp: (t) => 1.1 * (t < 0.2 ? (1 - Math.cos((Math.PI * t) / 0.2)) / 2 : 1),
    clear: (t) => (t < 0.16 ? 2 : 0.8),
    svd: (t) => 0.6 + 0.8 * Math.sin((Math.PI * t) / T) * (1 + 0.3 * Math.cos(omegaD(ALPHA) * t)),
  };
  const pulses = {};
  for (const [name, shape] of Object.entries(shapes)) {
    const epsOverG2 = centers.map(shape);
    const eps = epsOverG2.map((v) => sig(v * G2));
    const { t: ts, db } = linrespBuffer(edges, eps, ALPHA, T);
    const snr = KAPPA_B * trapz(ts, db.map((v) => v * v));
    // Mock cost proxy: (1/2T) * integral of (eps/g2)^2 dt, the same scale as gamma_x_rel - 1 above.
    const cost = (0.5 / T) * epsOverG2.reduce((s, v) => s + v * v * (T / nBins), 0);
    // CONTRACT §6.3 regex is lowercase-only; the brief writes T1.0us. Mock uses t1.0us.
    const snrId = `t2_4c.snr.td.two_mode.a2.10.p${name}.t1.0us`;
    const costId = `t2_4c.cost.linresp.two_mode.a2.10.p${name}`;
    const peak = Math.max(...epsOverG2);
    const tr = { Na: 24, Nb: 8 };
    records.push(
      rec({
        id: snrId, task: "2.4c", quantity: "snr", value: snr, units: "1", method: "two_mode_mesolve_trapz", params: stdParams(ALPHA, { eps_z_over_g2: sig(peak), pulse: name, T_us: T }),
        truncation: tr, convergence: conv("snr", snr, tr), cross_check: [xc("linresp", snr, snr * 1.02, 0.1)], script: "tasks/task_2_4c_verify.py",
      }),
      rec({
        id: costId, task: "2.4c", quantity: "cost", value: cost, units: "1", method: "linresp_cost_proxy", params: stdParams(ALPHA, { eps_z_over_g2: sig(peak), pulse: name, T_us: T }),
        convergence: null, cross_check: [xc("l4b_grid_interpolation", cost, cost * 1.05, 0.2)], script: "tasks/task_2_4c_pulses.py",
      }),
    );
    const keep = ts.map((_, i) => i).filter((i) => i % 10 === 0);
    pulses[name] = {
      t_us: edges,
      eps,
      snr: sig(snr),
      cost: sig(cost),
      id: `mock.${snrId}`,
      cost_id: `mock.${costId}`,
      snr_method: "td",
      signal: { t_us: keep.map((i) => sig(ts[i])), db_abs: keep.map((i) => sig(db[i])) },
    };
  }

  return {
    alpha: ALPHA,
    linresp: { freq_MHz: 3.14, Q: 2.46, t5: 0.73, t1: 1.13, id: `mock.${linId}` },
    signals,
    signals_by_eps: signalsByEps,
    tradeoff,
    pulses,
  };
}

// ---- verify (same derivation as the exporter's build_verify) ----
function buildVerify(records) {
  const convergence = [];
  const crossChecks = [];
  for (const r of records) {
    const c = r.convergence;
    if (c && c.sweeps) {
      for (const [axis, s] of Object.entries(c.sweeps)) {
        convergence.push({ id: r.id, axis, values: s.values, results: s.results, tol: c.rel_tol, converged: c.converged === true });
      }
    }
    for (const x of r.cross_check ?? []) {
      crossChecks.push({ id: r.id, method: x.method, rel_diff: x.rel_diff, tol: x.tol, agree: x.agree === true });
    }
  }
  return {
    generated_at: "MOCK",
    tests: { passed: 0, failed: 0, skipped: 0, source: "mock" },
    convergence,
    cross_checks: crossChecks,
  };
}

export function buildMock() {
  const records = [];
  const inflation = buildInflation(records);
  const errors = buildErrors(records);
  const readout = buildReadout(records);
  records.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  const verify = buildVerify(records);
  return { records, inflation, errors, readout, verify };
}

function main() {
  const outDir = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "data", "mock");
  mkdirSync(outDir, { recursive: true });
  const mock = buildMock();
  let total = 0;
  for (const [name, data] of Object.entries(mock)) {
    const text = JSON.stringify(data) + "\n";
    writeFileSync(join(outDir, `${name}.json`), text);
    total += text.length;
    console.log(`wrote src/data/mock/${name}.json  ${(text.length / 1e6).toFixed(3)} MB`);
  }
  console.log(`total ${(total / 1e6).toFixed(3)} MB (${mock.records.length} mock records)`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
