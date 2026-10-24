// Data loading. Every JSON file is bundled at build time (import.meta.glob, eager), never fetched, so
// the single-file build works from file://. Per file: live if present AND valid, else mock.
import type { Bundle, DataName, DuqRecord, ErrorsData, InflationData, ReadoutData, Source, VerifyData } from "./types";
import { DATA_NAMES } from "./types";
import { validateErrors, validateInflation, validateReadout, validateRecords, validateVerify } from "./validate";

export type Mods = Record<string, unknown>;

const live: Mods = import.meta.glob("./live/*.json", { eager: true, import: "default" });
const mock: Mods = import.meta.glob("./mock/*.json", { eager: true, import: "default" });

const VALIDATORS: Record<DataName, (x: unknown) => string[]> = {
  records: validateRecords,
  inflation: validateInflation,
  errors: validateErrors,
  readout: validateReadout,
  verify: validateVerify,
};

function find(mods: Mods, name: DataName): unknown {
  const key = Object.keys(mods).find((k) => k.endsWith(`/${name}.json`));
  return key === undefined ? undefined : mods[key];
}

export function loadBundle(liveMods: Mods = live, mockMods: Mods = mock): Bundle {
  const sources = {} as Record<DataName, Source>;
  const data = {} as Record<DataName, unknown>;
  const notes: string[] = [];

  for (const name of DATA_NAMES) {
    const l = find(liveMods, name);
    if (l !== undefined) {
      const errs = VALIDATORS[name](l);
      if (errs.length === 0) {
        sources[name] = "live";
        data[name] = l;
        continue;
      }
      notes.push(`live ${name}.json is invalid (${errs[0]}${errs.length > 1 ? `; +${errs.length - 1} more` : ""}), showing mock`);
    }
    const m = find(mockMods, name);
    if (m === undefined) throw new Error(`no live or mock ${name}.json bundled`);
    const errs = VALIDATORS[name](m);
    if (errs.length) notes.push(`mock ${name}.json is invalid (${errs[0]})`);
    sources[name] = "mock";
    data[name] = m;
  }

  const records = data.records as DuqRecord[];
  const byId = new Map<string, DuqRecord>(records.map((r) => [r.id, r]));
  // A mock page next to live records still needs its mock chips to resolve; mock ids never collide.
  if (DATA_NAMES.some((n) => n !== "records" && sources[n] === "mock") && sources.records === "live") {
    const mockRecords = find(mockMods, "records");
    if (Array.isArray(mockRecords)) for (const r of mockRecords as DuqRecord[]) if (!byId.has(r.id)) byId.set(r.id, r);
  }

  return {
    records,
    inflation: data.inflation as InflationData,
    errors: data.errors as ErrorsData,
    readout: data.readout as ReadoutData,
    verify: data.verify as VerifyData,
    sources,
    notes,
    byId,
  };
}
