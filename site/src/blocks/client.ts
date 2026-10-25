/** POST an ExprTree to the Academy API. The server accepts only this JSON shape. */

import type { ExprTree, Mode } from './expr.js';
import { EPS_D, G2, KAPPA_A, KAPPA_B } from '../sim/config.ts';

export interface ExprProgram {
  H: ExprTree;
  jumps: ExprTree[];
}

export function exprRequest(program: ExprProgram, modes: Mode): Record<string, unknown> {
  return {
    H: program.H,
    jumps: program.jumps,
    params: { g2: G2, eps_d: EPS_D, kappa_b: KAPPA_B, kappa_a: KAPPA_A },
    modes,
    ...(modes === 'one' ? { N: 8 } : { Na: 16, Nb: 5 }),
    init: 'vacuum',
    t_end_us: modes === 'one' ? 0.2 : 0.5,
    n_t: modes === 'one' ? 11 : 201,
    outputs: modes === 'one' ? ['n', 'parity'] : ['na', 'nb'],
  };
}

export async function postExpr(apiBase: string, program: ExprProgram, modes: Mode, fetchImpl: typeof fetch = fetch): Promise<unknown> {
  const response = await fetchImpl(`${apiBase.replace(/\/$/, '')}/api/sim/expr`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(exprRequest(program, modes)),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`expr ${response.status}: ${detail.slice(0, 180)}`);
  }
  return response.json();
}
