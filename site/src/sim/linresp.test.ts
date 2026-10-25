import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import * as C from './config.ts';
import { leakageProxy, optimalPulse, poles, pulseEnergy, response, snr } from './linresp.ts';
import { linspace } from './util.ts';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const fixtureDir = path.join(root, 'server/tests/fixtures/linresp');

function rel(a: number, b: number): number {
  return Math.abs(a - b) / Math.abs(b);
}

describe('linresp', () => {
  it('linresp_poles', () => {
    const found = poles(C.G2, C.KAPPA_B, C.ALPHA);
    const plus = found.find((p) => p.im > 0)!;
    const minus = found.find((p) => p.im < 0)!;
    expect(rel(plus.re, -4.08)).toBeLessThan(2e-3);
    expect(rel(plus.im, 19.72)).toBeLessThan(2e-3);
    expect(rel(minus.re, -4.08)).toBeLessThan(2e-3);
    expect(rel(minus.im, -19.72)).toBeLessThan(2e-3);
    const b = C.KAPPA_B / 2;
    const c = 4 * C.G2 * C.G2 * C.ALPHA * C.ALPHA;
    const disc = b * b - 4 * c;
    const re = -b / 2;
    const im = Math.sqrt(-disc) / 2;
    expect(Math.abs(plus.re - re)).toBeLessThan(1e-12);
    expect(Math.abs(plus.im - im)).toBeLessThan(1e-12);
  });

  it('dc_gain_and_memory_shift', () => {
    const eps = 0.2 * C.G2;
    const edges = linspace(0, 4, 2);
    const traj = response([eps], edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 2);
    const last = traj.tUs.length - 1;
    const bSs = -eps / (2 * C.G2 * C.ALPHA);
    const daIm = -eps / (2 * C.KAPPA_2 * C.ALPHA * C.ALPHA);
    expect(Math.abs(traj.b.re[last] - bSs)).toBeLessThan(1e-6);
    expect(Math.abs(traj.b.im[last])).toBeLessThan(1e-6);
    expect(Math.abs(traj.da.re[last])).toBeLessThan(1e-6);
    expect(Math.abs(traj.da.im[last] - daIm)).toBeLessThan(1e-6);
    const other = response([eps], edges, C.G2, C.KAPPA_B, C.ALPHA, -1, 2);
    expect(Math.abs(other.b.re[last] + bSs)).toBeLessThan(1e-6);
  });

  it('response_is_linear_and_obeys_the_ode', () => {
    const edges = linspace(0, 0.4, 3);
    const eps = Float64Array.from([0.15, -0.05]);
    const twice = Float64Array.from([0.3, -0.1]);
    const a = response(eps, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 801);
    const b = response(twice, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 801);
    let err = 0;
    for (let i = 0; i < a.tUs.length; i++) {
      err = Math.max(err, Math.abs(b.b.re[i] - 2 * a.b.re[i]), Math.abs(b.b.im[i] - 2 * a.b.im[i]));
      err = Math.max(err, Math.abs(b.da.re[i] - 2 * a.da.re[i]), Math.abs(b.da.im[i] - 2 * a.da.im[i]));
    }
    expect(err).toBeLessThan(1e-9);
    const s = 1;
    const g = C.G2;
    const alpha = C.ALPHA;
    const gamma = C.KAPPA_B / 2;
    let ode = 0;
    for (let i = 10; i < a.tUs.length - 10; i += 20) {
      const dt = a.tUs[i + 1] - a.tUs[i - 1];
      const bin = a.tUs[i] < edges[1] ? 0 : 1;
      const e = eps[bin];
      const dbr = (a.b.re[i + 1] - a.b.re[i - 1]) / dt;
      const dbi = (a.b.im[i + 1] - a.b.im[i - 1]) / dt;
      const dar = (a.da.re[i + 1] - a.da.re[i - 1]) / dt;
      const dai = (a.da.im[i + 1] - a.da.im[i - 1]) / dt;
      const cRe = 0;
      const cIm = -2 * s * g * alpha;
      const predBr = cRe * a.da.re[i] - cIm * a.da.im[i] - gamma * a.b.re[i];
      const predBi = cRe * a.da.im[i] + cIm * a.da.re[i] - gamma * a.b.im[i];
      const predAr = cRe * a.b.re[i] - cIm * a.b.im[i];
      const predAi = cRe * a.b.im[i] + cIm * a.b.re[i] - e;
      ode = Math.max(ode, Math.hypot(dbr - predBr, dbi - predBi), Math.hypot(dar - predAr, dai - predAi));
    }
    expect(ode).toBeLessThan(5e-3);
  });

  it('l8_optimal_beats_square', () => {
    const nBins = 20;
    const T = 1;
    const edges = linspace(0, T, nBins + 1);
    const amp = 0.5 * C.G2;
    const square = new Float64Array(nBins).fill(amp);
    const budget = pulseEnergy(edges, square);
    const plus = response(square, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 201);
    const minus = response(square, edges, C.G2, C.KAPPA_B, C.ALPHA, -1, 201);
    const dRe = new Float64Array(plus.tUs.length);
    const dIm = new Float64Array(plus.tUs.length);
    for (let i = 0; i < dRe.length; i++) {
      dRe[i] = plus.b.re[i] - minus.b.re[i];
      dIm[i] = plus.b.im[i] - minus.b.im[i];
    }
    const squareSnr = snr(plus.tUs, { re: dRe, im: dIm }, C.KAPPA_B);
    const opt = optimalPulse(nBins, T, C.G2, C.KAPPA_B, C.ALPHA);
    expect(Math.abs(pulseEnergy(edges, opt.epsBins) - 1)).toBeLessThan(1e-8);
    const scale = Math.sqrt(budget);
    const shaped = Float64Array.from(opt.epsBins, (v) => v * scale);
    expect(Math.abs(pulseEnergy(edges, shaped) - budget)).toBeLessThan(1e-8);
    const sp = response(shaped, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 201);
    const sm = response(shaped, edges, C.G2, C.KAPPA_B, C.ALPHA, -1, 201);
    const oRe = new Float64Array(sp.tUs.length);
    const oIm = new Float64Array(sp.tUs.length);
    for (let i = 0; i < oRe.length; i++) {
      oRe[i] = sp.b.re[i] - sm.b.re[i];
      oIm[i] = sp.b.im[i] - sm.b.im[i];
    }
    const optSnr = snr(sp.tUs, { re: oRe, im: oIm }, C.KAPPA_B);
    const leak = leakageProxy(sp.tUs, sp.da);
    console.log(`L8 square SNR ${squareSnr.toFixed(6)} optimal SNR ${optSnr.toFixed(6)} unit-energy gain ${opt.gain.toFixed(6)} leak ${leak.toExponential(3)}`);
    expect(squareSnr).toBeCloseTo(0.9541, 3);
    expect(optSnr).toBeCloseTo(4.0299, 3);
    expect(optSnr).toBeGreaterThan(squareSnr);
    expect(leak).toBeGreaterThan(0);
  });

  it('linresp_parity', () => {
    const names = ['square.json', 'cosramp.json', 'clear.json'];
    const present = names.every((name) => fs.existsSync(path.join(fixtureDir, name)));
    if (!present) {
      console.log('SKIP linresp_parity: server/tests/fixtures/linresp/*.json not present yet (P0)');
      return;
    }
    for (const name of names) {
      const raw = JSON.parse(fs.readFileSync(path.join(fixtureDir, name), 'utf8')) as {
        edges_us: number[];
        eps: number[];
        t_us: number[];
        delta_b_re: number[];
        delta_b_im: number[];
        snr: number;
        g2?: number;
        kappa_b?: number;
        alpha?: number;
      };
      const g2 = raw.g2 ?? C.G2;
      const kappaB = raw.kappa_b ?? C.KAPPA_B;
      const alpha = raw.alpha ?? C.ALPHA;
      const plus = response(raw.eps, raw.edges_us, g2, kappaB, alpha, 1, raw.t_us);
      const minus = response(raw.eps, raw.edges_us, g2, kappaB, alpha, -1, raw.t_us);
      let err = 0;
      for (let i = 0; i < raw.t_us.length; i++) {
        err = Math.max(err, Math.abs(plus.b.re[i] - minus.b.re[i] - raw.delta_b_re[i]));
        err = Math.max(err, Math.abs(plus.b.im[i] - minus.b.im[i] - raw.delta_b_im[i]));
      }
      const got = snr(plus.tUs, {
        re: Float64Array.from(raw.t_us, (_, i) => plus.b.re[i] - minus.b.re[i]),
        im: Float64Array.from(raw.t_us, (_, i) => plus.b.im[i] - minus.b.im[i]),
      }, kappaB);
      expect(err).toBeLessThan(1e-9);
      expect(Math.abs(got - raw.snr)).toBeLessThan(1e-9);
    }
  });
});
