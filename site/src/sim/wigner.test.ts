import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { zeros, type ComplexMatrix } from './complex.ts';
import { cat, coherent, fock, ketToRho } from './ops.ts';
import { linspace } from './util.ts';
import { wigner } from './wigner.ts';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const fixtureDir = path.join(root, 'server/tests/fixtures/wigner');

function analytic(x: number, y: number, bx = 0, by = 0): number {
  return (2 / Math.PI) * Math.exp(-2 * ((x - bx) ** 2 + (y - by) ** 2));
}

describe('wigner', () => {
  it('wigner_vacuum', () => {
    const rho = ketToRho(fock(30, 0));
    const x = linspace(-3, 3, 13);
    const y = linspace(-3, 3, 13);
    const w = wigner(rho, x, y);
    let err = 0;
    for (let ix = 0; ix < x.length; ix++) {
      for (let iy = 0; iy < y.length; iy++) {
        err = Math.max(err, Math.abs(w[ix * y.length + iy] - analytic(x[ix], y[iy])));
      }
    }
    const mid = 6 * y.length + 6;
    expect(Math.abs(w[mid] - 2 / Math.PI)).toBeLessThan(1e-9);
    expect(err).toBeLessThan(1e-9);
  });

  it('wigner_coherent_peak', () => {
    const rho = ketToRho(coherent(30, 2, 0));
    const x = linspace(-4, 4, 81);
    const y = linspace(-4, 4, 81);
    const w = wigner(rho, x, y);
    let max = -Infinity;
    let ix = 0;
    let iy = 0;
    let err = 0;
    for (let i = 0; i < x.length; i++) {
      for (let j = 0; j < y.length; j++) {
        const v = w[i * y.length + j];
        err = Math.max(err, Math.abs(v - analytic(x[i], y[j], 2, 0)));
        if (v > max) {
          max = v;
          ix = i;
          iy = j;
        }
      }
    }
    expect(x[ix]).toBeCloseTo(2, 8);
    expect(y[iy]).toBeCloseTo(0, 8);
    expect(err).toBeLessThan(1e-6);
  });

  it('wigner_cat_negative', () => {
    const rho = ketToRho(cat(30, 2, 1));
    const x = linspace(-4, 4, 81);
    const y = linspace(-4, 4, 81);
    const w = wigner(rho, x, y);
    let min = Infinity;
    for (let i = 0; i < w.length; i++) if (w[i] < min) min = w[i];
    expect(min).toBeLessThan(-0.2);
  });

  it('mixture_has_no_fringes', () => {
    const n = 30;
    const plus = ketToRho(coherent(n, 2, 0));
    const minus = ketToRho(coherent(n, -2, 0));
    const mix: ComplexMatrix = zeros(n);
    for (let k = 0; k < mix.data.length; k++) mix.data[k] = 0.5 * (plus.data[k] + minus.data[k]);
    const x = linspace(-4, 4, 81);
    const y = linspace(-4, 4, 41);
    const w = wigner(mix, x, y);
    let min = Infinity;
    for (let i = 0; i < w.length; i++) if (w[i] < min) min = w[i];
    expect(min).toBeGreaterThan(-0.02);
  });

  it('wigner_fixture_parity', () => {
    const files = ['vacuum.json', 'coherent2.json', 'catplus2.json'];
    const present = files.every((name) => fs.existsSync(path.join(fixtureDir, name)));
    if (!present) {
      console.log('SKIP wigner_fixture_parity: server/tests/fixtures/wigner/*.json not present yet (P0)');
      return;
    }
    for (const name of files) {
      const raw = JSON.parse(fs.readFileSync(path.join(fixtureDir, name), 'utf8')) as {
        x?: number[];
        y?: number[];
        w: number[] | number[][];
      };
      const x = Float64Array.from(raw.x ?? linspace(-4, 4, 81));
      const y = Float64Array.from(raw.y ?? linspace(-4, 4, 81));
      const rho =
        name === 'vacuum.json'
          ? ketToRho(fock(30, 0))
          : name === 'coherent2.json'
            ? ketToRho(coherent(30, 2, 0))
            : ketToRho(cat(30, 2, 1));
      const got = wigner(rho, x, y);
      const flat = Array.isArray(raw.w[0]) ? (raw.w as number[][]).flat() : (raw.w as number[]);
      expect(flat.length).toBe(got.length);
      let err = 0;
      for (let i = 0; i < got.length; i++) err = Math.max(err, Math.abs(got[i] - flat[i]));
      expect(err).toBeLessThan(1e-5);
    }
  });
});
