/** One-mode ExprTree evaluation. Two-mode symbols are rejected; the server owns those. */

import { adjoint, eye, mul, scale, zeros, type ComplexMatrix } from './complex.ts';
import { destroy, numberOp } from './ops.ts';
import { EPS_D, G2, KAPPA_B } from './config.ts';

export type ExprTree =
  | { op: 'num'; value: number; imag?: number }
  | { op: 'param'; name: string }
  | { op: 'sym'; name: string }
  | { op: 'add'; args: ExprTree[] }
  | { op: 'mul'; args: ExprTree[] }
  | { op: 'pow'; base: ExprTree; exp: number }
  | { op: 'dag'; arg: ExprTree }
  | { op: 'sqrt'; arg: ExprTree };

const PARAMS = new Set(['g2', 'eps_d', 'kappa_b', 'kappa_a', 'kappa2', 'alpha', 'eps_z', 'eps_x', 'K', 'chi']);
const SYMS = new Set(['a', 'ad', 'n_a', 'I']);

export interface ExprParams {
  kappa2: number;
  kappaA: number;
  alpha: number;
  epsZ?: number;
  epsX?: number;
}

export function paramTable(p: ExprParams): Record<string, number> {
  return {
    g2: G2,
    eps_d: EPS_D,
    kappa_b: KAPPA_B,
    kappa_a: p.kappaA,
    kappa2: p.kappa2,
    alpha: p.alpha,
    eps_z: p.epsZ ?? 0,
    eps_x: p.epsX ?? 0,
    K: 0,
    chi: 0,
  };
}

export function validateExpr(tree: ExprTree): void {
  let nodes = 0;
  const walk = (t: ExprTree, depth: number): void => {
    nodes += 1;
    if (depth > 8) throw new Error('ExprTree deeper than 8');
    if (nodes > 64) throw new Error('ExprTree has more than 64 nodes');
    switch (t.op) {
      case 'num':
        if (!Number.isFinite(t.value) || (t.imag !== undefined && !Number.isFinite(t.imag))) {
          throw new Error('num must be finite');
        }
        return;
      case 'param':
        if (!PARAMS.has(t.name)) throw new Error(`param '${t.name}' is not allowlisted`);
        return;
      case 'sym':
        if (t.name === 'b' || t.name === 'bd') {
          throw new Error('buffer symbols b and bd are two-mode; the browser solver is one-mode');
        }
        if (!SYMS.has(t.name)) throw new Error(`symbol '${t.name}' is not allowlisted`);
        return;
      case 'add':
      case 'mul':
        if (!Array.isArray(t.args) || t.args.length === 0) throw new Error(`${t.op} needs arguments`);
        for (const arg of t.args) walk(arg, depth + 1);
        return;
      case 'pow':
        if (!Number.isInteger(t.exp) || t.exp < 0 || t.exp > 4) throw new Error('pow exp must be an integer 0..4');
        walk(t.base, depth + 1);
        return;
      case 'dag':
        walk(t.arg, depth + 1);
        return;
      case 'sqrt':
        if (t.arg.op !== 'param' && t.arg.op !== 'num') throw new Error('sqrt applies only to a param or a num');
        walk(t.arg, depth + 1);
        return;
      default:
        throw new Error('unknown ExprTree op');
    }
  };
  walk(tree, 1);
}

export function evalExpr(tree: ExprTree, n: number, params: Record<string, number>): ComplexMatrix {
  validateExpr(tree);
  const cache = new Map<string, ComplexMatrix>();
  const sym = (name: string): ComplexMatrix => {
    const hit = cache.get(name);
    if (hit) return hit;
    let m: ComplexMatrix;
    if (name === 'a') m = destroy(n);
    else if (name === 'ad') m = adjoint(destroy(n));
    else if (name === 'n_a') m = numberOp(n);
    else m = eye(n);
    cache.set(name, m);
    return m;
  };
  const ev = (t: ExprTree): ComplexMatrix => {
    switch (t.op) {
      case 'num':
        return eye(n, t.value, t.imag ?? 0);
      case 'param': {
        const v = params[t.name];
        if (v === undefined) throw new Error(`param '${t.name}' has no value`);
        return eye(n, v, 0);
      }
      case 'sym':
        return sym(t.name);
      case 'add': {
        let acc = zeros(n);
        for (const arg of t.args) {
          const m = ev(arg);
          for (let k = 0; k < acc.data.length; k++) acc.data[k] += m.data[k];
        }
        return acc;
      }
      case 'mul': {
        let acc = ev(t.args[0]);
        for (let i = 1; i < t.args.length; i++) acc = mul(acc, ev(t.args[i]));
        return acc;
      }
      case 'pow': {
        if (t.exp === 0) return eye(n);
        let acc = ev(t.base);
        for (let i = 1; i < t.exp; i++) acc = mul(acc, ev(t.base));
        return acc;
      }
      case 'dag':
        return adjoint(ev(t.arg));
      case 'sqrt': {
        const scalar = ev(t.arg);
        const re = scalar.data[0];
        const im = scalar.data[1];
        if (im !== 0) throw new Error('sqrt of a complex coefficient is not used by the one-mode model');
        if (re < 0) throw new Error('sqrt of a negative rate');
        return scale(eye(n), Math.sqrt(re), 0);
      }
      default:
        throw new Error('unknown ExprTree op');
    }
  };
  return ev(tree);
}

/** Max |H − H†|. The contract rejects a non-Hermitian H above 1e-9. */
export function hermitianResidual(h: ComplexMatrix): number {
  const n = h.n;
  let worst = 0;
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const ij = 2 * (r * n + c);
      const ji = 2 * (c * n + r);
      const dr = h.data[ij] - h.data[ji];
      const di = h.data[ij + 1] + h.data[ji + 1];
      const a = Math.hypot(dr, di);
      if (a > worst) worst = a;
    }
  }
  return worst;
}
