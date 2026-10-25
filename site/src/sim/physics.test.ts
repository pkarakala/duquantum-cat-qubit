import { describe, expect, it } from 'vitest';
import { adjoint, mul, scale, sub, type ComplexMatrix } from './complex.ts';
import * as C from './config.ts';
import type { ExprTree } from './expr.ts';
import { cat, coherent, destroy, expectations, fock, ketToRho, rhoToVec } from './ops.ts';
import { simulate, simulateDetailed, type DetailedResult } from './simulate.ts';
import { bandMatvec, lindbladian } from './superop.ts';
import type { SimRequest } from './types.ts';
import { runInWorker } from './worker.ts';

function rel(a: number, b: number): number {
  return Math.abs(a - b) / Math.max(1e-30, Math.abs(b));
}

function masterDot(rho: ComplexMatrix, h: ComplexMatrix, jumps: ComplexMatrix[]): ComplexMatrix {
  const comm = sub(mul(h, rho), mul(rho, h));
  const out = scale(comm, 0, -1);
  const add = (src: ComplexMatrix, re: number) => {
    for (let k = 0; k < out.data.length; k++) out.data[k] += re * src.data[k];
  };
  for (const j of jumps) {
    const jd = adjoint(j);
    add(mul(mul(j, rho), jd), 1);
    const jdj = mul(jd, j);
    add(mul(jdj, rho), -0.5);
    add(mul(rho, jdj), -0.5);
  }
  return out;
}

function lossTree(rate: number): ExprTree {
  return {
    op: 'mul',
    args: [
      { op: 'sqrt', arg: { op: 'num', value: rate } },
      { op: 'sym', name: 'a' },
    ],
  };
}

function pairLossTree(): ExprTree {
  return {
    op: 'mul',
    args: [
      { op: 'sqrt', arg: { op: 'param', name: 'kappa2' } },
      { op: 'pow', base: { op: 'sym', name: 'a' }, exp: 2 },
    ],
  };
}

describe('lindblad and Crank–Nicolson', () => {
  it('master_equation_matches_superop', () => {
    const n = 4;
    const a = destroy(n);
    const ad = adjoint(a);
    const h = scale(sub(ad, a), 0, 0.3);
    const jumps = [scale(a, Math.sqrt(0.4), 0), scale(mul(a, a), Math.sqrt(1.7), 0)];
    const rho = ketToRho(coherent(n, 0.8, 0.2));
    const dot = masterDot(rho, h, jumps);
    const v = rhoToVec(rho);
    const y = new Float64Array(v.length);
    bandMatvec(lindbladian(h, jumps), v, y);
    const got = expectations(y, n);
    const ref = rhoToVec(dot);
    let err = 0;
    let mag = 0;
    for (let i = 0; i < y.length; i++) {
      err = Math.max(err, Math.abs(y[i] - ref[i]));
      mag = Math.max(mag, Math.abs(ref[i]));
    }
    expect(err).toBeLessThan(1e-10 * Math.max(1, mag));
    expect(Number.isFinite(got.n)).toBe(true);
  });

  it('non_hermitian_expr_is_rejected', () => {
    const req: SimRequest = {
      params: {
        N: 4,
        alpha: 1,
        kappa2: 0,
        kappaA: 0,
        H: { op: 'sym', name: 'a' },
        jumps: [],
      },
      init: { kind: 'vacuum' },
      tEndUs: 0.1,
      nT: 2,
      nSteps: 4,
      outputs: ['n'],
    };
    expect(() => simulate(req)).toThrow(/Hermitian/);
  });

  it('l1_coherent_and_fock', () => {
    const coherentRun = simulate({
      params: { N: 30, alpha: 2.1, kappa2: 0, kappaA: 0 },
      init: { kind: 'coherent', alpha: 2.1 },
      tEndUs: 0,
      nT: 1,
      outputs: ['n', 'wigner'],
    });
    expect(Math.abs(coherentRun.n![0] - 4.41)).toBeLessThan(1e-6);
    expect(coherentRun.finalPops[0]).toBeGreaterThan(0);
    expect(coherentRun.wigner?.frames).toHaveLength(1);
    const x = coherentRun.wigner!.x;
    const y = coherentRun.wigner!.y;
    const w = coherentRun.wigner!.frames[0].w;
    let max = -Infinity;
    let ix = 0;
    let iy = 0;
    for (let i = 0; i < x.length; i++) {
      for (let j = 0; j < y.length; j++) {
        const v = w[i * y.length + j];
        if (v > max) {
          max = v;
          ix = i;
          iy = j;
        }
      }
    }
    expect(x[ix]).toBeCloseTo(2.1, 5);
    expect(y[iy]).toBeCloseTo(0, 5);
    expect(max).toBeGreaterThan(0.6);
    const fockRun = simulate({
      params: { N: 12, alpha: 0, kappa2: 0, kappaA: 0 },
      init: { kind: 'fock', n: 4 },
      tEndUs: 0,
      nT: 1,
      outputs: ['n'],
    });
    expect(fockRun.n![0]).toBeCloseTo(4, 12);
    expect(fockRun.finalPops[4]).toBeCloseTo(1, 12);
    expect(fockRun.finalPops[3]).toBe(0);
  });

  it('decay_1_0a', () => {
    const rate = C.radPerUsFromMHz(1);
    const run = simulateDetailed({
      params: {
        N: 30,
        alpha: 2,
        kappa2: 0,
        kappaA: 0,
        H: { op: 'mul', args: [{ op: 'num', value: rate }, { op: 'sym', name: 'n_a' }] },
        jumps: [lossTree(rate)],
      },
      init: { kind: 'coherent', alpha: 2 },
      tEndUs: 1,
      nT: 21,
      nSteps: 4000,
      outputs: ['n', 're_a'],
    });
    let err = 0;
    for (let i = 0; i < run.tUs.length; i++) {
      const pred = 4 * Math.exp(-rate * run.tUs[i]);
      err = Math.max(err, Math.abs(run.n![i] - pred));
    }
    expect(err).toBeLessThan(1e-4);
  });

  it('l2_half_life_and_rotation', () => {
    const kappa = Math.log(2) / 0.5;
    const half = simulateDetailed({
      params: {
        N: 24,
        alpha: 2,
        kappa2: 0,
        kappaA: 0,
        H: { op: 'num', value: 0 },
        jumps: [lossTree(kappa)],
      },
      init: { kind: 'coherent', alpha: 2 },
      tEndUs: 0.5,
      nT: 2,
      nSteps: 2000,
      outputs: ['n'],
    });
    expect(Math.abs(half.n![1] - 2)).toBeLessThan(1e-3);
    expect(kappa).toBeGreaterThan(1.32);
    expect(kappa).toBeLessThan(1.46);
    const rate = C.radPerUsFromMHz(1);
    const rot = simulateDetailed({
      params: {
        N: 24,
        alpha: 2,
        kappa2: 0,
        kappaA: 0,
        H: { op: 'mul', args: [{ op: 'num', value: rate }, { op: 'sym', name: 'n_a' }] },
        jumps: [lossTree(rate)],
      },
      init: { kind: 'coherent', alpha: 2 },
      tEndUs: 0.25,
      nT: 2,
      nSteps: 2000,
      outputs: ['n', 're_a'],
    });
    const amp = 2 * Math.exp((-rate * 0.25) / 2);
    expect(Math.abs(rot.reA![1])).toBeLessThan(1e-3);
    expect(Math.abs(rot.imA[1] + amp)).toBeLessThan(1e-3);
    expect(Math.abs(rot.n![1] - amp * amp)).toBeLessThan(1e-4);
  });

  it('plateau_1_0b_parity_and_pops', () => {
    const run = simulateDetailed({
      params: {
        N: 30,
        alpha: 2,
        kappa2: C.KAPPA_2,
        kappaA: 0,
        H: { op: 'num', value: 0 },
        jumps: [pairLossTree()],
      },
      init: { kind: 'coherent', alpha: 2 },
      tEndUs: 3,
      nT: 31,
      nSteps: 600,
      outputs: ['n', 'parity'],
    });
    const pred = 0.5 * (1 - Math.exp(-8));
    expect(rel(run.n![run.n!.length - 1], 0.4998322686860546)).toBeLessThan(1e-4);
    expect(rel(run.n![run.n!.length - 1], pred)).toBeLessThan(1e-4);
    let drift = 0;
    for (let i = 0; i < run.parity!.length; i++) drift = Math.max(drift, Math.abs(run.parity![i] - run.parity![0]));
    expect(drift).toBeLessThan(1e-9);
    expect(Math.abs(run.finalPops[0] - 0.500167731313935)).toBeLessThan(1e-4);
    expect(Math.abs(run.finalPops[1] - 0.4998322686860522)).toBeLessThan(1e-4);
    for (let k = 2; k < run.finalPops.length; k++) expect(run.finalPops[k]).toBeLessThan(1e-6);
    expect(run.maxTraceError).toBeLessThan(1e-9);
    expect(run.finalHermAbs).toBeLessThan(1e-12);
  });

  it('l3_plateau_window_tracks_alpha', () => {
    const alpha = 1.07;
    const pred = 0.5 * (1 - Math.exp(-2 * alpha * alpha));
    const run = (kappa2: number): number =>
      simulate({
        params: {
          N: 16,
          alpha,
          kappa2,
          kappaA: 0,
          H: { op: 'num', value: 0 },
          jumps: [pairLossTree()],
        },
        init: { kind: 'coherent', alpha },
        tEndUs: 4,
        nT: 2,
        nSteps: 400,
        outputs: ['n'],
      }).n![1];
    const nominal = run(C.KAPPA_2);
    const slow = run(C.KAPPA_2 / 4);
    const fast = run(4 * C.KAPPA_2);
    expect(nominal).toBeGreaterThan(0.43);
    expect(nominal).toBeLessThan(0.47);
    expect(Math.abs(nominal - pred)).toBeLessThan(1e-3);
    expect(Math.abs(slow - nominal)).toBeLessThan(1e-3);
    expect(Math.abs(fast - nominal)).toBeLessThan(1e-3);
  });

  it('final_n_1_0c', () => {
    const scales = [0.25, 1, 4];
    const expectN = [4.387166478874212, 4.403969346892005, 4.408144076214539];
    scales.forEach((scale, i) => {
      const run = simulate({
        params: { N: 30, alpha: C.ALPHA, kappa2: scale * C.KAPPA_2, kappaA: C.KAPPA_A },
        init: { kind: 'vacuum' },
        tEndUs: 2,
        nT: 5,
        nSteps: 4000,
        outputs: ['n'],
      });
      const got = run.n![run.n!.length - 1];
      console.log(`1.0c scale ${scale} final n ${got} target ${expectN[i]} rel ${rel(got, expectN[i])}`);
      expect(rel(got, expectN[i])).toBeLessThan(1e-3);
    });
  });

  it('l4_cat_from_vacuum_and_loss', () => {
    const quiet = simulateDetailed({
      params: { N: 30, alpha: C.ALPHA, kappa2: C.KAPPA_2, kappaA: 0 },
      init: { kind: 'vacuum' },
      tEndUs: 1,
      nT: 5,
      nSteps: 400,
      outputs: ['n', 'parity'],
    });
    const nFinal = quiet.n![quiet.n!.length - 1];
    const pFinal = quiet.parity![quiet.parity!.length - 1];
    console.log(`L4 interactive n ${nFinal.toFixed(4)} parity ${pFinal.toFixed(4)} wall ${quiet.meta.wallMs.toFixed(1)} ms`);
    expect(nFinal).toBeGreaterThan(4.3);
    expect(nFinal).toBeLessThan(4.5);
    expect(pFinal).toBeGreaterThan(0.9);
    const rho = ketToRho(cat(30, C.ALPHA, 1));
    expect(expectations(rhoToVec(rho), 30).parity).toBeGreaterThan(0.99);
    const odd = expectations(rhoToVec(ketToRho(cat(30, C.ALPHA, -1))), 30);
    expect(odd.parity).toBeLessThan(-0.99);
    const noisy = simulate({
      params: { N: 30, alpha: C.ALPHA, kappa2: C.KAPPA_2, kappaA: 20 * C.KAPPA_A },
      init: { kind: 'vacuum' },
      tEndUs: 1,
      nT: 3,
      nSteps: 800,
      outputs: ['parity'],
    });
    expect(noisy.parity![noisy.parity!.length - 1]).toBeLessThan(0.2);
    expect(noisy.parity![noisy.parity!.length - 1]).toBeLessThan(pFinal);
  });

  it('drive_quadratures', () => {
    const eps = 0.2;
    const tEnd = 0.04;
    const base = {
      N: 16,
      alpha: 0,
      kappa2: 0,
      kappaA: 0,
      tEnd,
    };
    const z = simulateDetailed({
      params: { N: base.N, alpha: 0, kappa2: 0, kappaA: 0, epsZ: eps },
      init: { kind: 'vacuum' },
      tEndUs: tEnd,
      nT: 5,
      nSteps: 2000,
      outputs: ['re_a'],
    });
    const x = simulateDetailed({
      params: { N: base.N, alpha: 0, kappa2: 0, kappaA: 0, epsX: eps },
      init: { kind: 'vacuum' },
      tEndUs: tEnd,
      nT: 5,
      nSteps: 2000,
      outputs: ['re_a'],
    });
    const last = z.tUs.length - 1;
    expect(Math.abs(z.reA![last])).toBeLessThan(1e-6);
    expect(Math.abs(z.imA[last] + eps * z.tUs[last])).toBeLessThan(1e-5);
    expect(Math.abs(x.reA![last] - eps * x.tUs[last])).toBeLessThan(1e-5);
    expect(Math.abs(x.imA[last])).toBeLessThan(1e-6);
    const held = simulateDetailed({
      params: { N: 12, alpha: C.ALPHA, kappa2: C.KAPPA_2, kappaA: C.KAPPA_A, epsZ: 0.05 },
      init: { kind: 'vacuum' },
      tEndUs: 0.2,
      nT: 11,
      nSteps: 400,
      outputs: ['re_a'],
    });
    let maxRe = 0;
    for (let i = 0; i < held.reA!.length; i++) maxRe = Math.max(maxRe, Math.abs(held.reA![i]));
    expect(maxRe).toBeLessThan(1e-8);
  });

  it('trace_and_hermiticity', () => {
    const run = simulateDetailed({
      params: { N: 12, alpha: 1.4, kappa2: C.KAPPA_2, kappaA: C.KAPPA_A, epsX: 0.05, nTh: 0.02 },
      init: { kind: 'coherent', alpha: 1.2 },
      tEndUs: 0.5,
      nT: 11,
      nSteps: 300,
      outputs: ['n', 'parity'],
    });
    expect(run.maxTraceError).toBeLessThan(1e-9);
    expect(Math.abs(run.finalPops.reduce((s, p) => s + p, 0) - 1)).toBeLessThan(1e-9);
    expect(run.finalHermAbs).toBeLessThan(1e-12);
  });

  it('cn_matches_reference', () => {
    const steady = (nSteps: number): DetailedResult =>
      simulateDetailed({
        params: {
          N: 20,
          alpha: 2,
          kappa2: C.KAPPA_2,
          kappaA: 0,
          H: { op: 'num', value: 0 },
          jumps: [pairLossTree()],
        },
        init: { kind: 'coherent', alpha: 2 },
        tEndUs: 3,
        nT: 2,
        nSteps,
        outputs: ['n'],
      });
    const coarse = steady(200);
    const fine = steady(4000);
    const steadyErr = Math.abs(coarse.n![1] - fine.n![1]);
    expect(steadyErr).toBeLessThan(1e-5);
    const catRun = (nSteps: number, nT: number) =>
      simulate({
        params: { N: 20, alpha: C.ALPHA, kappa2: C.KAPPA_2, kappaA: C.KAPPA_A },
        init: { kind: 'vacuum' },
        tEndUs: 2,
        nT,
        nSteps,
        outputs: ['n'],
      });
    const mid = catRun(400, 201);
    const ref = catRun(4000, 201);
    let transient = 0;
    for (let i = 0; i < mid.n!.length; i++) transient = Math.max(transient, Math.abs(mid.n![i] - ref.n![i]));
    console.log(`CN steady |Δn| ${steadyErr.toExponential(2)}; 400-vs-4000 transient max |Δn| ${transient.toExponential(2)}`);
    expect(transient).toBeLessThan(2e-2);
  });

  it('expr_matches_standard_drive', () => {
    const eps = 0.15;
    const tree: ExprTree = {
      op: 'mul',
      args: [
        { op: 'num', value: eps },
        { op: 'add', args: [{ op: 'sym', name: 'a' }, { op: 'sym', name: 'ad' }] },
      ],
    };
    const via = simulateDetailed({
      params: { N: 8, alpha: 0, kappa2: 0, kappaA: 0, H: tree, jumps: [] },
      init: { kind: 'vacuum' },
      tEndUs: 0.05,
      nT: 2,
      nSteps: 400,
      outputs: ['re_a'],
    });
    const direct = simulateDetailed({
      params: { N: 8, alpha: 0, kappa2: 0, kappaA: 0, epsZ: eps },
      init: { kind: 'vacuum' },
      tEndUs: 0.05,
      nT: 2,
      nSteps: 400,
      outputs: ['re_a'],
    });
    expect(Math.abs(via.imA[1] - direct.imA[1])).toBeLessThan(1e-10);
    expect(Math.abs(via.reA![1] - direct.reA![1])).toBeLessThan(1e-10);
  });

  it('worker_matches_simulate', async () => {
    const req: SimRequest = {
      params: { N: 8, alpha: 1.2, kappa2: C.KAPPA_2, kappaA: C.KAPPA_A },
      init: { kind: 'vacuum' },
      tEndUs: 0.2,
      nT: 5,
      nSteps: 40,
      outputs: ['n', 'parity'],
    };
    const direct = simulate(req);
    const via = await runInWorker(req);
    expect(via.meta.engine).toBe('ts-cn');
    for (let i = 0; i < direct.n!.length; i++) {
      expect(via.n![i]).toBeCloseTo(direct.n![i], 10);
      expect(via.parity![i]).toBeCloseTo(direct.parity![i], 10);
    }
  });

  it('perf_n30', async () => {
    const req: SimRequest = {
      params: { N: 30, alpha: C.ALPHA, kappa2: C.KAPPA_2, kappaA: C.KAPPA_A },
      init: { kind: 'vacuum' },
      tEndUs: 2,
      nT: 21,
      nSteps: 400,
      outputs: ['n'],
    };
    const direct = simulate(req);
    const via = await runInWorker(req);
    console.log(`perf N=30 400 steps direct ${direct.meta.wallMs.toFixed(1)} ms, worker ${via.meta.wallMs.toFixed(1)} ms`);
    expect(direct.meta.wallMs).toBeLessThan(600);
    expect(via.meta.wallMs).toBeLessThan(600);
    expect(Math.abs(via.n![via.n!.length - 1] - direct.n![direct.n!.length - 1])).toBeLessThan(1e-9);
  });
});
