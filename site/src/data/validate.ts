// Shape validators for the five Lab files (CONTRACT §6.2, §13). Each returns [] when valid, else
// messages that start with the offending path (e.g. "records[3].id: ..."), so a bad live file can be
// named in the banner and the site can fall back to mock for it.
import { ID_RE } from "./types";

type Obj = Record<string, unknown>;
type Errs = string[];
const MAX_ERRORS = 50;

const isObj = (x: unknown): x is Obj => typeof x === "object" && x !== null && !Array.isArray(x);
const isNum = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);
const show = (x: unknown) => (typeof x === "number" ? String(x) : JSON.stringify(x)?.slice(0, 40) ?? String(x));

function push(errs: Errs, msg: string) {
  if (errs.length < MAX_ERRORS) errs.push(msg);
}

function obj(x: unknown, path: string, errs: Errs): x is Obj {
  if (isObj(x)) return true;
  push(errs, `${path}: expected object, got ${show(x)}`);
  return false;
}

function num(x: unknown, path: string, errs: Errs, nullable = false): boolean {
  if (isNum(x) || (nullable && x === null)) return true;
  push(errs, `${path}: expected finite number${nullable ? " or null" : ""}, got ${show(x)}`);
  return false;
}

function str(x: unknown, path: string, errs: Errs, nullable = false): boolean {
  if (typeof x === "string" || (nullable && x === null)) return true;
  push(errs, `${path}: expected string${nullable ? " or null" : ""}, got ${show(x)}`);
  return false;
}

function bool(x: unknown, path: string, errs: Errs): boolean {
  if (typeof x === "boolean") return true;
  push(errs, `${path}: expected boolean, got ${show(x)}`);
  return false;
}

function id(x: unknown, path: string, errs: Errs, nullable = false): boolean {
  if (nullable && x === null) return true;
  if (typeof x === "string" && ID_RE.test(x)) return true;
  push(errs, `${path}: expected a record id matching ${ID_RE.source}, got ${show(x)}`);
  return false;
}

function arr(x: unknown, path: string, errs: Errs): x is unknown[] {
  if (Array.isArray(x)) return true;
  push(errs, `${path}: expected array, got ${show(x)}`);
  return false;
}

function numArr(x: unknown, path: string, errs: Errs, opts: { len?: number; nullable?: boolean } = {}): x is number[] {
  if (!arr(x, path, errs)) return false;
  if (opts.len !== undefined && x.length !== opts.len) {
    push(errs, `${path}: expected length ${opts.len}, got ${x.length}`);
    return false;
  }
  for (let i = 0; i < x.length; i++) {
    const v = x[i];
    if (!(isNum(v) || (opts.nullable && v === null))) {
      push(errs, `${path}[${i}]: expected finite number${opts.nullable ? " or null" : ""}, got ${show(v)}`);
      return false;
    }
  }
  return true;
}

function optional(x: Obj, key: string, path: string, errs: Errs, check: (v: unknown, p: string, e: Errs) => unknown) {
  if (key in x && x[key] !== undefined) check(x[key], `${path}.${key}`, errs);
}

// ---- records.json ----

function validateConvergence(c: unknown, path: string, errs: Errs) {
  if (c === null) return;
  if (!obj(c, path, errs)) return;
  num(c.rel_tol, `${path}.rel_tol`, errs);
  bool(c.converged, `${path}.converged`, errs);
  optional(c, "key", path, errs, (v, p, e) => str(v, p, e));
  if (obj(c.sweeps, `${path}.sweeps`, errs)) {
    for (const [axis, s] of Object.entries(c.sweeps)) {
      const sp = `${path}.sweeps.${axis}`;
      if (!obj(s, sp, errs)) continue;
      if (numArr(s.values, `${sp}.values`, errs)) numArr(s.results, `${sp}.results`, errs, { len: s.values.length, nullable: true });
    }
  }
}

function validateCrossChecks(x: unknown, path: string, errs: Errs) {
  if (x === null) return;
  if (!arr(x, path, errs)) return;
  x.forEach((c, i) => {
    const p = `${path}[${i}]`;
    if (!obj(c, p, errs)) return;
    str(c.method, `${p}.method`, errs);
    num(c.rel_diff, `${p}.rel_diff`, errs, true);
    num(c.tol, `${p}.tol`, errs);
    bool(c.agree, `${p}.agree`, errs);
    optional(c, "value", p, errs, (v, pp, e) => num(v, pp, e, true));
    optional(c, "ref_id", p, errs, (v, pp, e) => str(v, pp, e, true));
  });
}

function validateRecord(r: unknown, path: string, errs: Errs) {
  if (!obj(r, path, errs)) return;
  if (r.schema !== "duq.record/v2") push(errs, `${path}.schema: expected "duq.record/v2", got ${show(r.schema)}`);
  id(r.id, `${path}.id`, errs);
  for (const k of ["task", "quantity", "units", "method"]) str(r[k], `${path}.${k}`, errs);
  if (typeof r.value === "boolean") push(errs, `${path}.value: expected finite number, got boolean`);
  else num(r.value, `${path}.value`, errs);
  obj(r.params, `${path}.params`, errs);
  optional(r, "uncertainty", path, errs, (v, p, e) => num(v, p, e, true));
  optional(r, "notes", path, errs, (v, p, e) => str(v, p, e, true));
  optional(r, "convergence", path, errs, validateConvergence);
  optional(r, "cross_check", path, errs, validateCrossChecks);
  for (const k of ["truncation", "numerics", "artifacts"]) {
    optional(r, k, path, errs, (v, p, e) => v === null || obj(v, p, e));
  }
  const pp = `${path}.provenance`;
  if (obj(r.provenance, pp, errs)) {
    str(r.provenance.script, `${pp}.script`, errs);
    str(r.provenance.git_commit, `${pp}.git_commit`, errs, true);
    bool(r.provenance.dirty, `${pp}.dirty`, errs);
  }
}

export function validateRecords(x: unknown): string[] {
  const errs: Errs = [];
  if (!arr(x, "records", errs)) return errs;
  const seen = new Set<unknown>();
  x.forEach((r, i) => {
    validateRecord(r, `records[${i}]`, errs);
    if (isObj(r) && typeof r.id === "string") {
      if (seen.has(r.id)) push(errs, `records[${i}].id: duplicate id ${r.id}`);
      seen.add(r.id);
    }
  });
  return errs;
}

// ---- inflation.json ----

export function validateInflation(x: unknown): string[] {
  const errs: Errs = [];
  const P = "inflation";
  if (!obj(x, P, errs)) return errs;
  if (numArr(x.t_us, `${P}.t_us`, errs)) {
    const n = x.t_us.length;
    for (const k of ["na", "nb", "top2_a", "top_b"]) numArr(x[k], `${P}.${k}`, errs, { len: n });
  }
  if (obj(x.effective, `${P}.effective`, errs)) {
    if (numArr(x.effective.t_us, `${P}.effective.t_us`, errs)) {
      numArr(x.effective.na, `${P}.effective.na`, errs, { len: x.effective.t_us.length });
    }
  }
  const W = `${P}.wigner`;
  if (obj(x.wigner, W, errs)) {
    const okX = numArr(x.wigner.x, `${W}.x`, errs);
    const okY = numArr(x.wigner.y, `${W}.y`, errs);
    const nx = okX ? (x.wigner.x as number[]).length : -1;
    const ny = okY ? (x.wigner.y as number[]).length : -1;
    if (nx > 81 || ny > 81) push(errs, `${W}: frames must be at most 81x81, got ${ny}x${nx}`);
    if (arr(x.wigner.frames, `${W}.frames`, errs)) {
      if (x.wigner.frames.length === 0) push(errs, `${W}.frames: expected at least one frame`);
      x.wigner.frames.forEach((f, k) => {
        const fp = `${W}.frames[${k}]`;
        if (!obj(f, fp, errs)) return;
        num(f.t_us, `${fp}.t_us`, errs);
        if (!arr(f.w, `${fp}.w`, errs)) return;
        if (ny >= 0 && f.w.length !== ny) push(errs, `${fp}.w: expected ${ny} rows (y.length), got ${f.w.length}`);
        for (let iy = 0; iy < f.w.length; iy++) {
          if (!numArr(f.w[iy], `${fp}.w[${iy}]`, errs, nx >= 0 ? { len: nx } : {})) break;
        }
      });
    }
  }
  if (arr(x.record_ids, `${P}.record_ids`, errs)) x.record_ids.forEach((v, i) => id(v, `${P}.record_ids[${i}]`, errs));
  optional(x, "alpha", P, errs, (v, p, e) => num(v, p, e));
  return errs;
}

// ---- errors.json ----

function ratePoints(x: unknown, path: string, errs: Errs) {
  if (!arr(x, path, errs)) return;
  x.forEach((p, i) => {
    const pp = `${path}[${i}]`;
    if (!obj(p, pp, errs)) return;
    num(p.alpha2, `${pp}.alpha2`, errs);
    num(p.value, `${pp}.value`, errs);
    num(p.unc, `${pp}.unc`, errs, true);
    id(p.id, `${pp}.id`, errs);
    optional(p, "model", pp, errs, (v, q, e) => str(v, q, e));
  });
}

function sameLengthArrays(x: unknown, path: string, keys: string[], errs: Errs, nullable: string[] = []) {
  if (!obj(x, path, errs)) return;
  const [first, ...rest] = keys;
  if (!numArr(x[first], `${path}.${first}`, errs)) return;
  const n = (x[first] as number[]).length;
  for (const k of rest) numArr(x[k], `${path}.${k}`, errs, { len: n, nullable: nullable.includes(k) });
}

export function validateErrors(x: unknown): string[] {
  const errs: Errs = [];
  const P = "errors";
  if (!obj(x, P, errs)) return errs;
  const GX = `${P}.gamma_x`;
  if (obj(x.gamma_x, GX, errs)) {
    const gx = x.gamma_x;
    for (const k of ["one_mode", "two_mode", "td"]) ratePoints(gx[k], `${GX}.${k}`, errs);
    sameLengthArrays(gx.analytic, `${GX}.analytic`, ["alpha2", "ch1", "ch2", "total"], errs);
    if (isObj(gx.analytic)) optional(gx.analytic, "source", `${GX}.analytic`, errs, (v, p, e) => str(v, p, e));
    if (obj(gx.thermal, `${GX}.thermal`, errs)) {
      for (const [nth, pts] of Object.entries(gx.thermal)) ratePoints(pts, `${GX}.thermal.${nth}`, errs);
    }
    optional(gx, "thermal_model", GX, errs, (v, p, e) => str(v, p, e));
    sameLengthArrays(gx.local_slope, `${GX}.local_slope`, ["alpha2", "one_mode", "two_mode"], errs, ["one_mode", "two_mode"]);
  }
  const GZ = `${P}.gamma_z`;
  if (obj(x.gamma_z, GZ, errs)) {
    ratePoints(x.gamma_z.td, `${GZ}.td`, errs);
    ratePoints(x.gamma_z.eig, `${GZ}.eig`, errs);
    sameLengthArrays(x.gamma_z.pred, `${GZ}.pred`, ["alpha2", "value"], errs);
  }
  return errs;
}

// ---- readout.json ----

function signals(x: unknown, path: string, errs: Errs, needEps: boolean) {
  sameLengthArrays(x, path, ["t_us", "b_plus_re", "b_plus_im", "b_minus_re", "b_minus_im"], errs);
  if (!isObj(x)) return;
  if (needEps) num(x.eps_over_g2, `${path}.eps_over_g2`, errs);
  else optional(x, "eps_over_g2", path, errs, (v, p, e) => num(v, p, e));
}

export function validateReadout(x: unknown): string[] {
  const errs: Errs = [];
  const P = "readout";
  if (!obj(x, P, errs)) return errs;
  num(x.alpha, `${P}.alpha`, errs);
  if (obj(x.linresp, `${P}.linresp`, errs)) {
    for (const k of ["freq_MHz", "Q", "t5", "t1"]) num(x.linresp[k], `${P}.linresp.${k}`, errs);
    optional(x.linresp, "id", `${P}.linresp`, errs, (v, p, e) => id(v, p, e, true));
  }
  signals(x.signals, `${P}.signals`, errs, false);
  if ("signals_by_eps" in x && x.signals_by_eps !== undefined) {
    if (arr(x.signals_by_eps, `${P}.signals_by_eps`, errs)) {
      x.signals_by_eps.forEach((s, i) => signals(s, `${P}.signals_by_eps[${i}]`, errs, true));
    }
  }
  if (arr(x.tradeoff, `${P}.tradeoff`, errs)) {
    x.tradeoff.forEach((t, i) => {
      const tp = `${P}.tradeoff[${i}]`;
      if (!obj(t, tp, errs)) return;
      for (const k of ["eps_over_g2", "snr_T1us", "gamma_x_rel"]) num(t[k], `${tp}.${k}`, errs);
      id(t.id, `${tp}.id`, errs, true);
      optional(t, "alpha", tp, errs, (v, p, e) => num(v, p, e));
      optional(t, "ok", tp, errs, (v, p, e) => bool(v, p, e));
    });
  }
  if (obj(x.pulses, `${P}.pulses`, errs)) {
    for (const [name, pulse] of Object.entries(x.pulses)) {
      const pp = `${P}.pulses.${name}`;
      if (!obj(pulse, pp, errs)) continue;
      if (numArr(pulse.eps, `${pp}.eps`, errs)) numArr(pulse.t_us, `${pp}.t_us`, errs, { len: pulse.eps.length + 1 });
      num(pulse.snr, `${pp}.snr`, errs);
      num(pulse.cost, `${pp}.cost`, errs);
      id(pulse.id, `${pp}.id`, errs, true);
      optional(pulse, "cost_id", pp, errs, (v, p, e) => id(v, p, e, true));
      optional(pulse, "snr_method", pp, errs, (v, p, e) => str(v, p, e));
      optional(pulse, "signal", pp, errs, (v, p, e) => sameLengthArrays(v, p, ["t_us", "db_abs"], e));
    }
  }
  return errs;
}

// ---- verify.json ----

export function validateVerify(x: unknown): string[] {
  const errs: Errs = [];
  const P = "verify";
  if (!obj(x, P, errs)) return errs;
  str(x.generated_at, `${P}.generated_at`, errs);
  if (obj(x.tests, `${P}.tests`, errs)) {
    for (const k of ["passed", "failed", "skipped"]) num(x.tests[k], `${P}.tests.${k}`, errs);
    optional(x.tests, "source", `${P}.tests`, errs, (v, p, e) => str(v, p, e, true));
  }
  if (arr(x.convergence, `${P}.convergence`, errs)) {
    x.convergence.forEach((c, i) => {
      const cp = `${P}.convergence[${i}]`;
      if (!obj(c, cp, errs)) return;
      id(c.id, `${cp}.id`, errs);
      str(c.axis, `${cp}.axis`, errs);
      if (numArr(c.values, `${cp}.values`, errs)) numArr(c.results, `${cp}.results`, errs, { len: c.values.length, nullable: true });
      num(c.tol, `${cp}.tol`, errs);
      bool(c.converged, `${cp}.converged`, errs);
    });
  }
  if (arr(x.cross_checks, `${P}.cross_checks`, errs)) {
    x.cross_checks.forEach((c, i) => {
      const cp = `${P}.cross_checks[${i}]`;
      if (!obj(c, cp, errs)) return;
      id(c.id, `${cp}.id`, errs);
      str(c.method, `${cp}.method`, errs);
      num(c.rel_diff, `${cp}.rel_diff`, errs, true);
      num(c.tol, `${cp}.tol`, errs);
      bool(c.agree, `${cp}.agree`, errs);
    });
  }
  optional(x, "claims", P, errs, (v, p, e) => {
    if (!obj(v, p, e)) return;
    for (const k of ["ok", "warn", "fail"]) num(v[k], `${p}.${k}`, e);
    if (arr(v.files, `${p}.files`, e)) v.files.forEach((f, i) => str(f, `${p}.files[${i}]`, e));
  });
  return errs;
}
