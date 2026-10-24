// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import {
  commitUrl,
  formatValue,
  isConverged,
  recordStatus,
  renderCard,
  renderChip,
} from "../src/components/provenance";
import type { DuqRecord } from "../src/data/types";

function baseRecord(): DuqRecord {
  return {
    schema: "duq.record/v2",
    id: "t2_1.gamma_x.eig.two_mode.a1.40.nth0",
    task: "2.1",
    quantity: "Gamma_X",
    value: 1.2021e-4,
    uncertainty: 2e-8,
    units: "1/us",
    method: "liouvillian_eig_odd_sector",
    params: { g2_MHz: 0.763, kappa_b_MHz: 2.6, kappa_a_kHz: 9.3, alpha: 1.4, n_th: 0 },
    truncation: { Na: 28, Nb: 8 },
    convergence: {
      key: "Gamma_X",
      rel_tol: 1e-3,
      sweeps: {
        Na: { fixed: { Nb: 8 }, values: [20, 24, 28, 32], results: [1.21e-4, 1.2022e-4, 1.2021e-4, 1.2021e-4] },
        Nb: { fixed: { Na: 28 }, values: [6, 8, 10], results: [1.202e-4, 1.2021e-4, 1.2021e-4] },
      },
      needed: { Na: 24, Nb: 6 },
      converged: true,
    },
    numerics: { rel_residual: 3e-7, edge_weight: 1e-9, cond_est: 120, sector: "odd", sigma: 0, k: 2 },
    cross_check: [
      { method: "time_domain_fit", ref_id: "t2_1.gamma_x.td.two_mode.a1.40", value: 1.19e-4, rel_diff: 0.009, tol: 0.02, agree: true },
    ],
    artifacts: { figure: "figures/task_2_1_gamma_x.png" },
    notes: "",
    provenance: {
      script: "tasks/task_2_1_eig.py",
      git_commit: "abc1234",
      git_branch: "standard-track",
      dirty: false,
      dynamiqs: "0.3.7",
      jax: "0.12.0.1",
      numpy: "2.3.0",
      scipy: "1.16.0",
      python: "3.12.13",
      platform: "macOS-14.5-arm64",
      cpu_count: 8,
      wall_s: 12.3,
      timestamp: "2026-10-24T23:10:00Z",
    },
  };
}

describe("recordStatus (mirrors the CONTRACT §11 claim rules)", () => {
  it("a converged, cross-checked, clean record is green", () => {
    expect(recordStatus(baseRecord())).toEqual({ status: "green", reasons: [] });
  });

  const cases: [string, (r: DuqRecord) => void, string][] = [
    ["converged false", (r) => (r.convergence!.converged = false), "not converged"],
    ["no cross-checks", (r) => (r.cross_check = []), "no agreeing cross-check"],
    ["all cross-checks disagree", (r) => (r.cross_check![0].agree = false), "no agreeing cross-check"],
    ["dirty tree", (r) => (r.provenance!.dirty = true), "dirty working tree"],
    ["no provenance", (r) => delete r.provenance, "no provenance"],
  ];
  for (const [label, mutate, reason] of cases) {
    it(`${label} is amber with reason "${reason}"`, () => {
      const r = baseRecord();
      mutate(r);
      const s = recordStatus(r);
      expect(s.status).toBe("amber");
      expect(s.reasons).toContain(reason);
    });
  }

  it("convergence null needs a non-empty notes justification", () => {
    const r = baseRecord();
    r.convergence = null;
    r.notes = "analytic, truncation-independent";
    expect(isConverged(r)).toBe(true);
    r.notes = "";
    expect(isConverged(r)).toBe(false);
    r.notes = null;
    expect(isConverged(r)).toBe(false);
  });
});

describe("formatting helpers", () => {
  it("commitUrl links a sha and refuses placeholders", () => {
    expect(commitUrl("abc1234")).toBe("https://github.com/pkarakala/duquantum-cat-qubit/commit/abc1234");
    expect(commitUrl(null)).toBe(null);
    expect(commitUrl("mock")).toBe(null);
  });

  it("formatValue uses 5 significant figures and exponent form outside [1e-3, 1e4)", () => {
    expect(formatValue(1.2021e-4, 2e-8)).toBe("1.2021e-4 ± 2.0e-8");
    expect(formatValue(0.5135, null)).toBe("0.51350");
    expect(formatValue(6.894411732563246, null)).toBe("6.8944");
    expect(formatValue(12345.6, null)).toBe("1.2346e+4");
    expect(formatValue(0.5135, 0.0021)).toBe("0.51350 ± 0.0021");
  });
});

describe("renderCard", () => {
  it("shows every provenance field of a green record", () => {
    const r = baseRecord();
    const el = renderCard(r);
    const text = el.textContent ?? "";
    expect(el.dataset.status).toBe("green");
    expect(text).toContain("verified");
    for (const s of [r.id, "1/us", "liouvillian_eig_odd_sector", "Na", "0.001", "time_domain_fit", "0.3.7", "2026-10-24T23:10:00Z"]) {
      expect(text).toContain(s);
    }
    const links = [...el.querySelectorAll("a")].map((a) => a.getAttribute("href"));
    expect(links).toContain("https://github.com/pkarakala/duquantum-cat-qubit/commit/abc1234");
  });

  it("shows amber reasons as text, not colour alone", () => {
    const r = baseRecord();
    r.convergence!.converged = false;
    r.provenance!.dirty = true;
    const el = renderCard(r);
    expect(el.dataset.status).toBe("amber");
    const text = el.textContent ?? "";
    expect(text).toContain("not converged");
    expect(text).toContain("dirty working tree");
    expect(text).toContain("needs review");
    expect(text).not.toContain("verified");
  });

  it("renders a wrapped intro record with null versions as n/a", () => {
    const r = baseRecord();
    r.convergence = null;
    r.notes = "wrapped from flat JSON results/task_1_1.json";
    Object.assign(r.provenance!, { dynamiqs: null, git_branch: null, jax: null, platform: null, cpu_count: null });
    const el = renderCard(r);
    expect(el.textContent).toContain("n/a");
    expect(el.dataset.status).toBe("green");
  });

  it("renderChip names its record and status for assistive tech", () => {
    const r = baseRecord();
    const chip = renderChip(r.id, new Map([[r.id, r]]));
    expect(chip.getAttribute("aria-label")).toContain(r.id);
    expect(chip.dataset.status).toBe("green");
    const missing = renderChip("t9.nope.eig.one_mode", new Map());
    expect(missing.getAttribute("aria-label")).toContain("t9.nope.eig.one_mode");
    expect(missing.dataset.status).toBe("missing");
  });
});
