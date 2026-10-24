// Provenance cards. The green check mirrors the claims checker (CONTRACT §11 rules 4-6): converged,
// at least one agreeing cross-check, and produced from a clean working tree. Anything else is amber,
// and the reasons are always spelled out in text (never colour alone).
import type { DuqRecord } from "../data/types";
import { h, scrollTable } from "../lib/dom";

export const REPO_URL = "https://github.com/pkarakala/duquantum-cat-qubit";
const SHA_RE = /^[0-9a-f]{7,40}$/i;

export type Status = "green" | "amber";

export function isConverged(r: DuqRecord): boolean {
  if (r.convergence === null) return typeof r.notes === "string" && r.notes.trim() !== "";
  return r.convergence?.converged === true;
}

export function recordStatus(r: DuqRecord): { status: Status; reasons: string[] } {
  const reasons: string[] = [];
  if (!isConverged(r)) reasons.push("not converged");
  if (!(r.cross_check ?? []).some((c) => c.agree === true)) reasons.push("no agreeing cross-check");
  if (!r.provenance) reasons.push("no provenance");
  else if (r.provenance.dirty !== false) reasons.push(r.provenance.dirty === true ? "dirty working tree" : "dirty flag missing");
  return { status: reasons.length ? "amber" : "green", reasons };
}

export function commitUrl(sha: string | null): string | null {
  return sha && SHA_RE.test(sha) ? `${REPO_URL}/commit/${sha}` : null;
}

const useExponent = (v: number) => v !== 0 && (Math.abs(v) < 1e-3 || Math.abs(v) >= 1e4);

export function formatNumber(v: number): string {
  if (!Number.isFinite(v)) return String(v);
  if (v === 0) return "0";
  return useExponent(v) ? v.toExponential(4) : v.toPrecision(5);
}

export function formatValue(v: number, unc: number | null): string {
  const s = formatNumber(v);
  if (unc === null || unc === undefined || !Number.isFinite(unc)) return s;
  return `${s} ± ${useExponent(v) ? unc.toExponential(1) : unc.toPrecision(2)}`;
}

export const isMockRecord = (r: DuqRecord) => r.id.startsWith("mock.");
const na = (v: unknown): string => (v === null || v === undefined || v === "" ? "n/a" : typeof v === "number" ? formatNumber(v) : String(v));
const show = (v: unknown): string =>
  v === null || v === undefined ? "n/a" : typeof v === "number" ? formatNumber(v) : typeof v === "object" ? JSON.stringify(v) : String(v);

function dl(rows: [string, Node | string][]): HTMLDListElement {
  return h("dl", { class: "kv" }, ...rows.flatMap(([k, v]) => [h("dt", {}, k), h("dd", {}, v)]));
}

function statusLine(status: Status, reasons: string[]): HTMLElement {
  if (status === "green") {
    return h("p", { class: "badge", "data-status": "green" }, h("span", { "aria-hidden": "true" }, "✓ "), "verified: converged, cross-checked, clean tree");
  }
  return h(
    "div",
    { class: "badge", "data-status": "amber" },
    h("p", {}, h("span", { "aria-hidden": "true" }, "⚠ "), "needs review:"),
    h("ul", { class: "reasons" }, ...reasons.map((x) => h("li", {}, x))),
  );
}

function convergenceSection(r: DuqRecord): HTMLElement {
  const c = r.convergence;
  if (c === null) return h("p", {}, "No truncation sweep (truncation-independent). Justification: ", h("q", {}, na(r.notes)));
  if (c === undefined) return h("p", {}, "No convergence block.");
  const needed = c.needed ? Object.entries(c.needed).map(([k, v]) => `${k} ≥ ${na(v)}`).join(", ") : "n/a";
  const rows = Object.entries(c.sweeps).map(([axis, s]) =>
    h(
      "tr",
      {},
      h("th", { scope: "row" }, axis),
      h("td", {}, s.fixed ? Object.entries(s.fixed).map(([k, v]) => `${k} = ${v}`).join(", ") : ""),
      h("td", {}, s.values.join(", ")),
      h("td", {}, s.results.map((v) => (v === null ? "n/a" : formatNumber(v))).join(", ")),
    ),
  );
  return h(
    "div",
    {},
    dl([
      ["key", na(c.key)],
      ["rel_tol", String(c.rel_tol)],
      ["needed", needed],
      ["converged", c.converged ? "yes" : "no"],
    ]),
    rows.length
      ? scrollTable(
          h("table", {}, h("thead", {}, h("tr", {}, h("th", { scope: "col" }, "axis"), h("th", { scope: "col" }, "fixed"), h("th", { scope: "col" }, "values"), h("th", { scope: "col" }, "results"))), h("tbody", {}, ...rows)),
          "Convergence sweeps",
        )
      : null,
  );
}

function crossCheckSection(r: DuqRecord): HTMLElement {
  const xs = r.cross_check ?? [];
  if (!xs.length) return h("p", {}, "No cross-checks.");
  const rows = xs.map((x) =>
    h(
      "tr",
      { "data-agree": String(x.agree) },
      h("th", { scope: "row" }, x.method),
      h("td", {}, x.ref_id ? h("code", {}, x.ref_id) : "n/a"),
      h("td", {}, show(x.value)),
      h("td", {}, show(x.rel_diff)),
      h("td", {}, show(x.tol)),
      h("td", {}, x.agree ? "✓ agrees" : "✗ disagrees"),
    ),
  );
  return scrollTable(
    h(
      "table",
      {},
      h("thead", {}, h("tr", {}, ...["method", "ref", "value", "rel_diff", "tol", "agree"].map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, ...rows),
    ),
    "Cross-checks",
  );
}

const PROV_KEYS = ["script", "git_commit", "git_branch", "dirty", "dynamiqs", "jax", "numpy", "scipy", "python", "platform", "cpu_count", "wall_s", "timestamp"];

function provenanceSection(r: DuqRecord): HTMLElement {
  const p = r.provenance;
  if (!p) return h("p", {}, "No provenance block.");
  const rows: [string, Node | string][] = [];
  const all = p as unknown as Record<string, unknown>;
  for (const k of [...PROV_KEYS, ...Object.keys(p).filter((k) => !PROV_KEYS.includes(k))]) {
    if (k === "git_commit") {
      const url = commitUrl(p.git_commit);
      rows.push(["commit", url ? h("a", { href: url, target: "_blank", rel: "noopener" }, p.git_commit ?? "") : `${na(p.git_commit)} (no link)`]);
    } else if (k === "dirty") {
      rows.push(["dirty", p.dirty === false ? "no (clean tree)" : p.dirty === true ? "yes" : "n/a"]);
    } else {
      rows.push([k, na(all[k])]);
    }
  }
  return dl(rows);
}

export function renderCard(r: DuqRecord): HTMLElement {
  const { status, reasons } = recordStatus(r);
  const params = Object.entries(r.params ?? {});
  const numerics = Object.entries(r.numerics ?? {});
  const artifacts = Object.entries(r.artifacts ?? {}).filter(([, v]) => v);
  const trunc = r.truncation ? Object.entries(r.truncation).map(([k, v]) => `${k} = ${v}`).join(", ") : "n/a";
  return h(
    "article",
    { class: "card", "data-status": status },
    statusLine(status, reasons),
    isMockRecord(r) ? h("p", { class: "mock-tag" }, "MOCK record: synthetic placeholder, not a result.") : null,
    h("h2", { class: "card-title" }, `${r.quantity} · Task ${r.task}`),
    h("p", {}, h("code", { class: "rid" }, r.id)),
    h("p", { class: "value" }, formatValue(r.value, r.uncertainty ?? null), " ", h("span", { class: "units" }, r.units)),
    dl([
      ["method", r.method],
      ["truncation", trunc],
    ]),
    h("h3", {}, "Convergence"),
    convergenceSection(r),
    h("h3", {}, "Cross-checks"),
    crossCheckSection(r),
    params.length ? h("h3", {}, "Parameters") : null,
    params.length ? dl(params.map(([k, v]) => [k, show(v)])) : null,
    numerics.length ? h("h3", {}, "Numerics") : null,
    numerics.length ? dl(numerics.map(([k, v]) => [k, show(v)])) : null,
    h("h3", {}, "Provenance"),
    provenanceSection(r),
    artifacts.length ? h("h3", {}, "Artifacts") : null,
    artifacts.length ? h("ul", {}, ...artifacts.map(([k, v]) => h("li", {}, `${k}: `, h("code", {}, String(v))))) : null,
    r.notes ? h("p", { class: "notes" }, "Notes: ", r.notes) : null,
  );
}

export function renderChip(id: string, byId: Map<string, DuqRecord>): HTMLElement {
  const r = byId.get(id);
  if (!r) {
    return h("span", { class: "chip", "data-status": "missing", "aria-label": `No record found for ${id}`, title: "record not in this bundle" }, `? ${id}`);
  }
  const { status, reasons } = recordStatus(r);
  const label = status === "green" ? "verified" : `needs review (${reasons.join(", ")})`;
  return h(
    "button",
    {
      type: "button",
      class: "chip",
      "data-status": status,
      "aria-label": `Open provenance card for ${id}: ${label}`,
      title: `${id}: ${label}`,
      onclick: () => openCard(id, byId),
    },
    h("span", { class: "chip-mark", "aria-hidden": "true" }, status === "green" ? "✓" : "⚠"),
    h("span", { class: "chip-id" }, id),
  );
}

export function openCard(id: string, byId: Map<string, DuqRecord>): void {
  const r = byId.get(id);
  if (!r) return;
  let dlg = document.getElementById("card") as HTMLDialogElement | null;
  if (!dlg) {
    dlg = document.createElement("dialog");
    dlg.id = "card";
    document.body.append(dlg);
  }
  const d = dlg;
  const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const close = () => (typeof d.close === "function" ? d.close() : d.removeAttribute("open"));
  const closeBtn = h("button", { type: "button", class: "close", "aria-label": "Close provenance card", onclick: close }, "Close");
  d.replaceChildren(closeBtn, renderCard(r));
  d.setAttribute("aria-label", `Provenance card for ${id}`);
  d.onclose = () => opener?.focus();
  d.onclick = (ev) => {
    if (ev.target === d) close(); // click on the backdrop
  };
  d.onkeydown = (ev) => {
    if (ev.key === "Escape" && typeof d.showModal !== "function") close();
  };
  if (typeof d.showModal === "function") {
    if (!d.open) d.showModal();
  } else {
    d.setAttribute("open", "");
  }
  closeBtn.focus();
}
