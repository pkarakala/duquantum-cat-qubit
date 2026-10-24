import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, describe, expect, it } from "vitest";
import {
  validateErrors,
  validateInflation,
  validateReadout,
  validateRecords,
  validateVerify,
} from "../src/data/validate";

const REPO = fileURLToPath(new URL("../../", import.meta.url));
const FIXTURES = "site/test/fixtures/results";
const PY = process.env.DUQ_PY;
const VALIDATORS: Record<string, (x: unknown) => string[]> = {
  records: validateRecords,
  inflation: validateInflation,
  errors: validateErrors,
  readout: validateReadout,
  verify: validateVerify,
};

const tmps: string[] = [];
function tmp(): string {
  const d = mkdtempSync(join(tmpdir(), "duq-lab-"));
  tmps.push(d);
  return d;
}
afterAll(() => tmps.forEach((d) => rmSync(d, { recursive: true, force: true })));

function exportLab(...args: string[]) {
  const r = spawnSync(PY!, ["-m", "tools.export_lab_data", ...args], {
    cwd: REPO,
    encoding: "utf8",
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  });
  return { code: r.status, out: `${r.stdout}\n${r.stderr}` };
}
const readJson = (p: string) => JSON.parse(readFileSync(p, "utf8"));

describe("tools/export_lab_data.py is stdlib + numpy only", () => {
  it("never imports src.* (which would pull in dynamiqs)", () => {
    const code = readFileSync(join(REPO, "tools/export_lab_data.py"), "utf8");
    expect(code).not.toMatch(/^\s*(from|import)\s+src\b/m);
    const allowed = new Set([
      "__future__", "argparse", "datetime", "glob", "json", "math", "os", "pathlib", "re", "sys",
      "typing", "xml", "numpy", "tools",
    ]);
    for (const m of code.matchAll(/^\s*(?:from|import)\s+([A-Za-z_][\w.]*)/gm)) {
      expect(allowed.has(m[1].split(".")[0]), m[0]).toBe(true);
    }
  });
});

describe.skipIf(!PY)("exporter against fixtures (DUQ_PY)", () => {
  it("writes valid files with the 3-frame Wigner fixture and reports omissions", () => {
    const out = tmp();
    const r = exportLab("--results", FIXTURES, "--out", out);
    expect(r.code, r.out).toBe(0);
    const written = readdirSync(out).sort();
    expect(written).toEqual(["errors.json", "inflation.json", "records.json", "verify.json"]);
    for (const f of written) {
      const name = f.replace(/\.json$/, "");
      expect(VALIDATORS[name](readJson(join(out, f))), f).toEqual([]);
    }
    const inf = readJson(join(out, "inflation.json"));
    expect(inf.wigner.frames.length).toBe(3);
    expect(inf.wigner.frames[0].w.length).toBe(5);
    expect(inf.record_ids).toEqual(["t1_1.peak_na.td.two_mode.a2.10"]);
    expect(r.out).toContain("omitted readout.json");
    expect(r.out).toMatch(/total/i);
    const err = readJson(join(out, "errors.json"));
    expect(err.gamma_x.analytic.source).toBe("exporter_closed_form_RESEARCH_5");
    expect(err.gamma_x.analytic.alpha2.length).toBe(200);
    expect(err.gamma_z.pred.value.length).toBe(err.gamma_z.td.length);
    const recs = readJson(join(out, "records.json"));
    expect(recs.map((x: { id: string }) => x.id)).toEqual([...recs.map((x: { id: string }) => x.id)].sort());
    expect(recs.length).toBe(4);
  });

  it("the size gate (--max-mb 0.0001) exits 1 and writes nothing", () => {
    const out = join(tmp(), "live");
    const r = exportLab("--results", FIXTURES, "--out", out, "--max-mb", "0.0001");
    expect(r.code, r.out).toBe(1);
    expect(existsSync(out) ? readdirSync(out) : []).toEqual([]);
  });

  it("--dry-run writes nothing", () => {
    const out = join(tmp(), "live");
    const r = exportLab("--results", FIXTURES, "--out", out, "--dry-run");
    expect(r.code, r.out).toBe(0);
    expect(existsSync(out) ? readdirSync(out) : []).toEqual([]);
  });

  it("a missing npz omits inflation.json and removes a stale one", () => {
    const root = tmp();
    const results = join(root, "results");
    cpSync(join(REPO, FIXTURES), results, { recursive: true });
    rmSync(join(results, "arrays", "lab.inflation_wigner.npz"));
    const out = join(root, "live");
    mkdirSync(out, { recursive: true });
    const stale = join(out, "inflation.json");
    writeFileSync(stale, "{}");
    const r = exportLab("--results", results, "--out", out);
    expect(r.code, r.out).toBe(0);
    expect(existsSync(stale)).toBe(false);
    expect(r.out).toContain("omitted inflation.json");
  });

  it("prefers results/index.json over the records directory and reads --junit", () => {
    const root = tmp();
    const results = join(root, "results");
    cpSync(join(REPO, FIXTURES), results, { recursive: true });
    const recs = readdirSync(join(results, "records"))
      .sort()
      .slice(0, 2)
      .map((f) => readJson(join(results, "records", f)));
    writeFileSync(
      join(results, "index.json"),
      JSON.stringify({ schema: "duq.index/v1", generated_at: "2026-10-24T23:00:00Z", count: 2, records: recs }),
    );
    const junit = join(root, "junit.xml");
    writeFileSync(
      junit,
      `<?xml version="1.0"?><testsuites><testsuite name="pytest" tests="10" failures="1" errors="1" skipped="2"></testsuite></testsuites>`,
    );
    const out = join(root, "live");
    const r = exportLab("--results", results, "--out", out, "--junit", junit);
    expect(r.code, r.out).toBe(0);
    expect(readJson(join(out, "records.json")).length).toBe(2);
    const v = readJson(join(out, "verify.json"));
    expect(v.tests).toMatchObject({ passed: 6, failed: 2, skipped: 2, source: "junit" });
  });
});
