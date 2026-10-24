import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildMock } from "../scripts/make_mock.mjs";
import { DATA_NAMES, type ReadoutData, type SignalsAtEps } from "../src/data/types";
import { defaultEpsIndex, epsGrid } from "../src/lib/readout";
import { wignerRange } from "../src/lib/wigner";

describe("wignerRange", () => {
  it("is symmetric and fixed over all frames", () => {
    expect(wignerRange([{ w: [[0.1, -0.3]] }, { w: [[0.2, 0.05]] }])).toEqual([-0.3, 0.3]);
  });
  it("never collapses to a zero range", () => {
    const [lo, hi] = wignerRange([{ w: [[0, 0]] }]);
    expect(hi).toBeGreaterThan(0);
    expect(lo).toBe(-hi);
  });
});

describe("readout slider grid", () => {
  const sig = (eps: number): SignalsAtEps => ({
    eps_over_g2: eps,
    t_us: [0, 1],
    b_plus_re: [0, -eps],
    b_plus_im: [0, 0],
    b_minus_re: [0, eps],
    b_minus_im: [0, 0],
  });
  const base = buildMock().readout as ReadoutData;

  it("maps slider index i to signals_by_eps sorted by eps_over_g2", () => {
    const shuffled = [sig(2), sig(0.05), sig(1), sig(0.5)];
    const r: ReadoutData = { ...base, signals_by_eps: shuffled };
    const grid = epsGrid(r);
    expect(grid.map((s) => s.eps_over_g2)).toEqual([0.05, 0.5, 1, 2]);
    expect(grid[2]).toBe(shuffled[2]);
    expect(shuffled.map((s) => s.eps_over_g2)).toEqual([2, 0.05, 1, 0.5]);
  });

  it("starts at the epsilon nearest 1 g2", () => {
    const r: ReadoutData = { ...base, signals_by_eps: [sig(0.2), sig(3), sig(0.9), sig(2)] };
    expect(epsGrid(r)[defaultEpsIndex(epsGrid(r))].eps_over_g2).toBe(0.9);
  });

  it("falls back to the single signals entry without signals_by_eps", () => {
    const r: ReadoutData = { ...base, signals_by_eps: undefined, signals: { ...sig(1) } };
    expect(epsGrid(r)).toHaveLength(1);
    expect(epsGrid(r)[0].eps_over_g2).toBe(1);
  });
});

describe("committed mock files are fresh", () => {
  it("buildMock() deep-equals site/src/data/mock/*.json", () => {
    const mock = buildMock() as Record<string, unknown>;
    for (const name of DATA_NAMES) {
      const path = fileURLToPath(new URL(`../src/data/mock/${name}.json`, import.meta.url));
      const committed = JSON.parse(readFileSync(path, "utf8"));
      expect(committed, `${name}.json is stale: run npm run mock`).toEqual(JSON.parse(JSON.stringify(mock[name])));
    }
  });

  it("is deterministic and carries no wall-clock time", () => {
    expect(JSON.stringify(buildMock())).toBe(JSON.stringify(buildMock()));
    expect((buildMock().verify as { generated_at: string }).generated_at).toBe("MOCK");
  });
});
