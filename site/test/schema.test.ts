import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { buildMock } from "../scripts/make_mock.mjs";
import {
  validateErrors,
  validateInflation,
  validateReadout,
  validateRecords,
  validateVerify,
} from "../src/data/validate";
import { DATA_NAMES, ID_RE, type DataName } from "../src/data/types";

const VALIDATORS: Record<DataName, (x: unknown) => string[]> = {
  records: validateRecords,
  inflation: validateInflation,
  errors: validateErrors,
  readout: validateReadout,
  verify: validateVerify,
};

const liveDir = fileURLToPath(new URL("../src/data/live/", import.meta.url));
const clone = <T>(x: T): T => structuredClone(x);
type Any = any;

describe("mock data passes every validator", () => {
  const mock = buildMock() as Record<DataName, unknown>;
  for (const name of DATA_NAMES) {
    it(`mock ${name}.json is valid`, () => {
      expect(VALIDATORS[name](mock[name])).toEqual([]);
    });
  }
});

describe("live data (if exported) passes every validator", () => {
  for (const name of DATA_NAMES) {
    const path = `${liveDir}${name}.json`;
    it.skipIf(!existsSync(path))(`live ${name}.json is valid`, () => {
      const data = JSON.parse(readFileSync(path, "utf8"));
      expect(VALIDATORS[name](data)).toEqual([]);
    });
  }
});

describe("mutations fail with a path in the message", () => {
  const mock = buildMock() as Any;

  it("records[0].id deleted", () => {
    const recs = clone(mock.records);
    delete recs[0].id;
    const errs = validateRecords(recs);
    expect(errs.length).toBeGreaterThan(0);
    expect(errs.join("\n")).toContain("records[0].id");
  });

  it("a Wigner row one element short", () => {
    const inf = clone(mock.inflation);
    inf.wigner.frames[0].w[0].pop();
    const errs = validateInflation(inf);
    expect(errs.length).toBeGreaterThan(0);
    expect(errs.join("\n")).toContain("frames[0]");
  });

  it("a non-numeric Gamma_X value", () => {
    const err = clone(mock.errors);
    err.gamma_x.one_mode[0].value = "x";
    const errs = validateErrors(err);
    expect(errs.length).toBeGreaterThan(0);
    expect(errs.join("\n")).toContain("one_mode[0].value");
  });

  it("a NaN trade-off point", () => {
    const ro = clone(mock.readout);
    ro.tradeoff[0].gamma_x_rel = NaN;
    const errs = validateReadout(ro);
    expect(errs.length).toBeGreaterThan(0);
    expect(errs.join("\n")).toContain("tradeoff[0].gamma_x_rel");
  });

  it("a bad record id and a wrong schema tag", () => {
    const recs = clone(mock.records);
    recs[1].id = "Bad ID!";
    recs[2].schema = "duq.record/v1";
    const msg = validateRecords(recs).join("\n");
    expect(msg).toContain("records[1].id");
    expect(msg).toContain("records[2].schema");
  });

  it("a pulse whose edges do not bracket its bins", () => {
    const ro = clone(mock.readout);
    const name = Object.keys(ro.pulses)[0];
    ro.pulses[name].t_us.pop();
    expect(validateReadout(ro).join("\n")).toContain(`pulses.${name}.t_us`);
  });

  it("a verify file without generated_at", () => {
    const v = clone(mock.verify);
    delete v.generated_at;
    expect(validateVerify(v).join("\n")).toContain("verify.generated_at");
  });
});

describe("mock ids and cross-references", () => {
  const mock = buildMock() as Any;
  const ids = new Set<string>(mock.records.map((r: Any) => r.id));

  it("every record id matches the CONTRACT §6.3 regex and starts with mock.", () => {
    for (const r of mock.records) {
      expect(r.id).toMatch(ID_RE);
      expect(r.id.startsWith("mock.")).toBe(true);
    }
    expect(ids.size).toBe(mock.records.length);
  });

  it("every id referenced by inflation/errors/readout resolves in records", () => {
    const refs: string[] = [...mock.inflation.record_ids];
    const gx = mock.errors.gamma_x;
    for (const list of [gx.one_mode, gx.two_mode, gx.td, ...Object.values(gx.thermal as Record<string, Any[]>)]) {
      for (const p of list as Any[]) refs.push(p.id);
    }
    for (const p of [...mock.errors.gamma_z.td, ...mock.errors.gamma_z.eig]) refs.push(p.id);
    for (const t of mock.readout.tradeoff) if (t.id) refs.push(t.id);
    for (const p of Object.values(mock.readout.pulses as Record<string, Any>)) {
      if (p.id) refs.push(p.id);
      if (p.cost_id) refs.push(p.cost_id);
    }
    if (mock.readout.linresp.id) refs.push(mock.readout.linresp.id);
    for (const row of [...mock.verify.convergence, ...mock.verify.cross_checks]) refs.push(row.id);
    expect(refs.length).toBeGreaterThan(50);
    for (const id of refs) expect(ids.has(id), id).toBe(true);
  });

  it("Wigner frames are <= 81x81 and match the x/y axes", () => {
    const { x, y, frames } = mock.inflation.wigner;
    expect(x.length).toBeLessThanOrEqual(81);
    expect(y.length).toBeLessThanOrEqual(81);
    for (const f of frames) {
      expect(f.w.length).toBe(y.length);
      expect(f.w[0].length).toBe(x.length);
    }
  });

  it("the whole mock bundle is < 8,000,000 characters of JSON", () => {
    const total = DATA_NAMES.reduce((n, k) => n + JSON.stringify(mock[k]).length, 0);
    expect(total).toBeLessThan(8_000_000);
  });
});
