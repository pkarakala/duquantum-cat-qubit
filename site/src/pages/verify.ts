import { renderChip } from "../components/provenance";
import type { Bundle } from "../data/types";
import { h, scrollTable, uniqueId } from "../lib/dom";

const HOWTO = [
  '& $env:DUQ_PY -m pytest -m "not slow" -q',
  "bash run_all.sh --quick",
  "& $env:DUQ_PY -m tools.build_index",
  "& $env:DUQ_PY -m tools.check_claims",
  "& $env:DUQ_PY -m tools.export_lab_data",
  "npm --prefix site ci; npm --prefix site run build:single",
].join("\n");

type Row = Record<string, string | number | boolean | null>;

function sortRows(rows: Row[], key: string, dir: 1 | -1): Row[] {
  return [...rows].sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    if (av === bv) return 0;
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    return (av < bv ? -1 : 1) * dir;
  });
}

function sortableTable(cols: { key: string; label: string }[], rows: Row[], label: string, renderCell: (row: Row, key: string) => Node | string): HTMLElement {
  let sortKey = cols[0]?.key ?? "id";
  let dir: 1 | -1 = 1;
  const host = h("div", {});

  const draw = () => {
    const sorted = sortRows(rows, sortKey, dir);
    const head = cols.map((c) => {
      const th = h("th", { scope: "col", class: "sortable", role: "columnheader", "aria-sort": c.key === sortKey ? (dir === 1 ? "ascending" : "descending") : "none" }, c.label);
      const btn = h("button", { type: "button", "aria-label": `Sort by ${c.label}` }, c.label);
      th.replaceChildren(btn);
      th.setAttribute("aria-sort", c.key === sortKey ? (dir === 1 ? "ascending" : "descending") : "none");
      btn.addEventListener("click", () => {
        if (sortKey === c.key) dir = dir === 1 ? -1 : 1;
        else {
          sortKey = c.key;
          dir = 1;
        }
        draw();
      });
      return th;
    });
    const body = sorted.map((row) => h("tr", {}, ...cols.map((c) => h("td", {}, renderCell(row, c.key)))));
    host.replaceChildren(
      scrollTable(
        h("table", {}, h("thead", {}, h("tr", {}, ...head)), h("tbody", {}, ...body)),
        label,
      ),
    );
  };
  draw();
  return host;
}

export function render(root: HTMLElement, b: Bundle): void {
  const v = b.verify;
  const ran = v.tests.source && v.tests.source !== "mock" && v.tests.source !== "null";
  const summary = ran
    ? `Tests: ${v.tests.passed} passed, ${v.tests.failed} failed, ${v.tests.skipped} skipped (source: ${v.tests.source}).`
    : "Tests: not run.";

  const convRows: Row[] = v.convergence.map((c) => ({
    id: c.id,
    axis: c.axis,
    values: c.values.join(", "),
    results: c.results.map((x) => (x === null ? "n/a" : String(x))).join(", "),
    tol: c.tol,
    converged: c.converged,
  }));
  const xcRows: Row[] = v.cross_checks.map((c) => ({
    id: c.id,
    method: c.method,
    rel_diff: c.rel_diff,
    tol: c.tol,
    agree: c.agree,
  }));

  const copyId = uniqueId("copy");
  const copyBtn = h("button", { type: "button", id: copyId, "aria-label": "Copy how-to-reproduce commands" }, "Copy commands");
  const pre = h("pre", { class: "howto", tabindex: 0 }, HOWTO);
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(HOWTO);
      copyBtn.textContent = "Copied";
    } catch {
      copyBtn.textContent = "Copy failed — select the block";
    }
  });

  const claims = v.claims
    ? `Claims check: ${v.claims.ok} ok, ${v.claims.warn} warn, ${v.claims.fail} fail${v.claims.files.length ? ` (${v.claims.files.join(", ")})` : ""}.`
    : "Claims check: not run.";

  root.append(
    h("h1", {}, "Verification"),
    h("p", { class: "lede" }, "Convergence sweeps, independent cross-checks, and the commands that rebuild this Lab from the repo."),
    h("p", {}, summary),
    h("p", {}, `Generated at ${v.generated_at}.`),
    h("p", {}, claims),
    h("h2", {}, "Convergence"),
    sortableTable(
      [
        { key: "id", label: "id" },
        { key: "axis", label: "axis" },
        { key: "values", label: "values" },
        { key: "results", label: "results" },
        { key: "tol", label: "tol" },
        { key: "converged", label: "converged" },
      ],
      convRows,
      "Convergence table",
      (row, key) => {
        if (key === "id") return renderChip(String(row.id), b.byId);
        if (key === "converged") return row.converged ? "yes" : "no";
        return String(row[key] ?? "");
      },
    ),
    h("h2", {}, "Cross-checks"),
    sortableTable(
      [
        { key: "id", label: "id" },
        { key: "method", label: "method" },
        { key: "rel_diff", label: "rel_diff" },
        { key: "tol", label: "tol" },
        { key: "agree", label: "agree" },
      ],
      xcRows,
      "Cross-check table",
      (row, key) => {
        if (key === "id") return renderChip(String(row.id), b.byId);
        if (key === "agree") {
          return h("span", { class: row.agree ? "agree-yes" : "agree-no" }, row.agree ? "✓ agrees" : "✗ disagrees");
        }
        return row[key] === null || row[key] === undefined ? "n/a" : String(row[key]);
      },
    ),
    h("h2", {}, "How to reproduce"),
    h("div", { class: "row" }, copyBtn),
    pre,
  );
}
